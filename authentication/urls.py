from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, PasswordResetRequestView, PasswordResetConfirmView,
    ChangePasswordView, UserProfileView, DeleteAccountView
)

router = DefaultRouter()

urlpatterns = [
    path('v1/', include([
        path('register/', RegisterView.as_view(), name='register'),
        path('login/', LoginView.as_view(), name='login'),
        path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
        path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
        path('change-password/', ChangePasswordView.as_view(), name='change-password'),
        path('profile/', UserProfileView.as_view(), name='user-profile'),
        path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),
        path('', include(router.urls)),
    ])),
]

