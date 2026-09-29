from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

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
        token, _ = Token.objects.get_or_create(user=serializer.validated_data['user'])
        return Response(LoginResponseSerializer({'token': token.key}).data)