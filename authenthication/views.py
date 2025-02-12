from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.auth.model import Token
from rest_framework.permissions import AllowAny, isAuthenticated
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .serializers import UserSerializer, LoginSerializer, PasswordResetSerializer, UserProfileSerializer
from django.contrib.auth import get_user_model

from authenthication import serializers

User = get_user_model()

class RegisterView(generics.CreateAPIView)
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

