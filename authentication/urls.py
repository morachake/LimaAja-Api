from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, PasswordResetRequestView, PasswordResetConfirmView,
    ChangePasswordView, UserProfileView, DeleteAccountView, CustomTokenObtainPairView,
    LogoutView, TokenVerifyView, UserDetailsView, EmailVerificationView,
    ResendEmailVerificationView
)

urlpatterns = [
    path('v1/', include([
        path('register/', RegisterView.as_view(), name='register'),
        path('login/', CustomTokenObtainPairView.as_view(), name='login'),
        path('logout/', LogoutView.as_view(), name='logout'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
        path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
        path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
        path('change-password/', ChangePasswordView.as_view(), name='change-password'),
        path('profile/', UserProfileView.as_view(), name='user-profile'),
        path('user-details/', UserDetailsView.as_view(), name='user-details'),
        path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),
        path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
        path('resend-verification-email/', ResendEmailVerificationView.as_view(), name='resend-verification-email'),
    ])),
]

