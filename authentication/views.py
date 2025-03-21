from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from .serializers import (
    UserSerializer, LoginSerializer, PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer, ChangePasswordSerializer, UserProfileSerializer,
    CustomTokenObtainPairSerializer, TokenVerifySerializer, EmailVerificationSerializer,
    UserDetailsSerializer, CooperativeApprovalSerializer, AdminLoginAsCooperativeSerializer,LogoutSerializer,
    CooperativeProfileSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        if user.role == 'cooperative':
            user.is_approved = False
            user.save()
            # Notify admin about new cooperative registration
            send_mail(
                'New Cooperative Registration',
                f'A new cooperative has registered and needs approval: {user.email}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
        else:
            user.is_approved = True
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(email=request.data['email'])
            if user.role == 'cooperative' and not user.is_approved:
                return Response({"error": "Your cooperative account is pending approval."}, status=status.HTTP_403_FORBIDDEN)
        return response

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = get_random_string(length=32)
            user.password_reset_token = token
            user.password_reset_token_created_at = timezone.now()
            user.save()
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{token}"
            send_mail(
                'Password Reset',
                f'Click the following link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return Response({"success": "Password reset email has been sent."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        try:
            user = User.objects.get(password_reset_token=token)
            if (timezone.now() - user.password_reset_token_created_at).days > 1:
                return Response({"error": "Password reset token has expired."}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_created_at = None
            user.save()
            return Response({"success": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"error": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"success": "Password updated successfully."}, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class CooperativeProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CooperativeProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        if self.request.user.role != 'cooperative':
            return Response({"error": "Only cooperatives can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

class DeleteAccountView(generics.DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.soft_delete()
        return Response({"success": "Account has been deleted."}, status=status.HTTP_200_OK)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = LogoutSerializer  # Add the serializer class

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"success": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": "Successfully logged out."}, status=status.HTTP_200_OK)
    
    def get(self, request):
        # For browser-based logout, we don't need to validate any data
        # Just return a success response
        return Response({"success": "Successfully logged out."}, status=status.HTTP_200_OK)

class TokenVerifyView(generics.GenericAPIView):
    serializer_class = TokenVerifySerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data['token'])
            return Response({"valid": True}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"valid": False}, status=status.HTTP_400_BAD_REQUEST)

class UserDetailsView(generics.RetrieveAPIView):
    serializer_class = UserDetailsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

class EmailVerificationView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email_verification_token=serializer.validated_data['token'])
            if (timezone.now() - user.email_verification_token_created_at).days > 1:
                return Response({"error": "Email verification token has expired."}, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.email_verification_token = None
            user.email_verification_token_created_at = None
            user.save()
            return Response({"success": "Email has been verified successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

class ResendEmailVerificationView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            if user.is_active:
                return Response({"error": "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST)
            token = get_random_string(length=32)
            user.email_verification_token = token
            user.email_verification_token_created_at = timezone.now()
            user.save()
            verification_link = f"{settings.FRONTEND_URL}/verify-email/{token}"
            send_mail(
                'Email Verification',
                f'Click the following link to verify your email: {verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return Response({"success": "Email verification link has been sent."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)


class CooperativeApprovalView(generics.GenericAPIView):
    serializer_class = CooperativeApprovalSerializer
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']
        is_approved = serializer.validated_data['is_approved']

        try:
            user = User.objects.get(id=user_id, role='cooperative')
            user.is_approved = is_approved
            user.save()
            return Response({"success": f"Cooperative approval status updated to {is_approved}"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Cooperative not found"}, status=status.HTTP_404_NOT_FOUND)

class AdminLoginAsCooperativeView(generics.GenericAPIView):
    serializer_class = AdminLoginAsCooperativeSerializer
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cooperative_id = serializer.validated_data['cooperative_id']

        try:
            cooperative = User.objects.get(id=cooperative_id, role='cooperative')
            refresh = RefreshToken.for_user(cooperative)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            })
        except User.DoesNotExist:
            return Response({"error": "Cooperative not found"}, status=status.HTTP_404_NOT_FOUND)

