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
    
    def create(slef,request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response ({
            "user": UserSerializer(user,context=slef.get_serializer_context()).data,
            "token": token.key
        })
class LoginView(generics.GenericAPIview):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(email=serializer.validate_data['email'])
        if user :
            token,created = Token.objects.get_or_create(user=user)
            return Response({
                "user": UserSerializer(user,context=self.get_serializer_context()).data,
                "token": token.key
            })
    return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


