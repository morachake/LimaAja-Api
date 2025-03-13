from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_approved', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # check if user already exists with the same phone number
         # Check if a user with this phone number already exists
        try:
            existing_user = self.model.objects.get(phone_number=phone_number)
            # If we're creating a superuser with the same email as an existing user,
            # we'll update that user instead of creating a new one
            if existing_user.email == email:
                for key, value in extra_fields.items():
                    setattr(existing_user, key, value)
                existing_user.set_password(password)
                existing_user.save(using=self._db)
                return existing_user
            else:
                # If the phone number is taken by a different user, append a suffix to make it unique
                import random
                phone_number = f"{phone_number}_{random.randint(1000, 9999)}"
        except self.model.DoesNotExist:
            pass

        
        return self.create_user(email, full_name, phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('cooperative', 'Cooperative'),
        ('buyer', 'Buyer'),
        ('admin', 'Admin'),
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    profile_picture = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    # Cooperative specific fields
    certificates = models.JSONField(blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)

    # Buyer specific fields
    payment_methods = models.JSONField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number']

    def __str__(self):
        return self.email

    def soft_delete(self):
        self.is_deleted = True
        self.save()

