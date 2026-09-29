from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


phone_number_validator = RegexValidator(
    regex=r'^\+?996\d{9}$',
    message='Enter a phone number in the format 996XXXXXXXXX or +996XXXXXXXXX.',
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=['password'])
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields.get('is_staff'):
            raise ValueError('A superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('A superuser must have is_superuser=True.')
        if not extra_fields.get('phone_number'):
            raise ValueError('A phone number is required for a superuser.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    birthdate = models.DateField(null=True, blank=True)
    phone_number = models.CharField(
        max_length=13,
        blank=True,
        validators=[phone_number_validator],
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)
        if self.is_superuser and not self.phone_number:
            raise ValidationError({'phone_number': 'A phone number is required for a superuser.'})

    def __str__(self):
        return self.email