import json
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from common.redis_store import confirm_confirmation_code, save_confirmation_code
from .serializers import (
    ConfirmRegistrationSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    RegisterSerializer,
)


User = get_user_model()


def _google_request(url, data=None, headers=None):
    request = Request(url, data=data, headers=headers or {})
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read())


def _google_userinfo(code):
    token_data = _google_request(
        'https://oauth2.googleapis.com/token',
        data=urlencode({
            'code': code,
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }).encode(),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    access_token = token_data.get('access_token')
    if not access_token:
        raise ValueError('Google did not return an access token.')
    return _google_request(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
    )


def _jwt_response(user):
    refresh = RefreshToken.for_user(user)
    refresh['birthdate'] = user.birthdate.isoformat() if user.birthdate else None
    return LoginResponseSerializer(
        {'access': str(refresh.access_token), 'refresh': str(refresh)}
    ).data


@extend_schema_view(
    post=extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterSerializer},
        summary='Register with email and password',
    )
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)
        code = f'{secrets.randbelow(1_000_000):06d}'
        save_confirmation_code(user.pk, code)
        send_mail(
            'Confirm your Shop API account',
            f'Your confirmation code is {code}. It expires in 5 minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


class ConfirmRegistrationView(generics.GenericAPIView):
    serializer_class = ConfirmRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        request=ConfirmRegistrationSerializer,
        responses={200: None},
        summary='Confirm registration with a one-time code',
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data['email'],
            is_active=False,
        ).first()
        if user is None or not confirm_confirmation_code(
            user.pk,
            serializer.validated_data['code'],
        ):
            return Response(
                {'detail': 'Invalid or expired confirmation code.'},
                status=400,
            )

        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'detail': 'Account confirmed.'})


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
        summary='Log in with email and password',
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return Response(_jwt_response(user))


class GoogleOAuthStartView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
        redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '')
        if not client_id or not settings.GOOGLE_OAUTH_CLIENT_SECRET or not redirect_uri:
            return Response({'detail': 'Google OAuth is not configured.'}, status=503)

        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state
        authorization_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
        })
        return Response({'authorization_url': authorization_url})


class GoogleOAuthCallbackView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        expected_state = request.session.pop('google_oauth_state', None)
        supplied_state = request.query_params.get('state', '')
        code = request.query_params.get('code', '')
        if not expected_state or not constant_time_compare(expected_state, supplied_state):
            return Response({'detail': 'Invalid OAuth state.'}, status=400)
        if not code:
            return Response({'detail': 'Authorization code is required.'}, status=400)

        try:
            profile = _google_userinfo(code)
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
            return Response({'detail': 'Could not authenticate with Google.'}, status=400)

        email = profile.get('email')
        if not email or profile.get('verified_email') is not True:
            return Response({'detail': 'Google account must have a verified email.'}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': profile.get('given_name', ''),
                'last_name': profile.get('family_name', ''),
                'registration_source': 'google',
                'is_active': True,
            },
        )
        user.first_name = profile.get('given_name', '')
        user.last_name = profile.get('family_name', '')
        user.is_active = True
        user.last_login = timezone.now()
        update_fields = ['first_name', 'last_name', 'is_active', 'last_login']
        if created:
            user.set_unusable_password()
            update_fields.append('password')
        user.save(update_fields=update_fields)
        return Response(_jwt_response(user))