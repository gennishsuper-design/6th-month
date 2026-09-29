from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginResponseSerializer, LoginSerializer, RegisterSerializer


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
        refresh = RefreshToken.for_user(user)
        refresh['birthdate'] = user.birthdate.isoformat() if user.birthdate else None
        return Response(
            LoginResponseSerializer(
                {'access': str(refresh.access_token), 'refresh': str(refresh)}
            ).data
        )