from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import phone_number_validator


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[phone_number_validator],
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            email=attrs['email'],
            password=attrs['password'],
        )
        if user is None:
            raise serializers.ValidationError('Invalid email or password.')
        attrs['user'] = user
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()