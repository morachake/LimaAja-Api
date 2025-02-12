from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, PasswordResetView, PasswordResetConfirmView, Pass
)