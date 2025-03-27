from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number', 'password', 'password2', 'role', 
                  'profile_picture', 'address', 'city', 'province', 'postal_code', 'country', 
                  'certificates', 'payment_details', 'payment_methods', 'is_approved',
                  'registration_number', 'tax_id', 'year_established', 'cooperative_type', 'website',
                  'manager_name', 'manager_email', 'manager_phone', 'manager_role', 'manager_bio',
                  'contact_name', 'contact_email', 'contact_phone', 'contact_role')
        extra_kwargs = {
            'full_name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
            'role': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
    
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, write_only=True)

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number', 'role', 'profile_picture', 
                  'address', 'city', 'province', 'postal_code', 'country', 
                  'created_at', 'updated_at', 'certificates', 'payment_details', 
                  'payment_methods', 'is_approved', 'registration_number', 'tax_id', 
                  'year_established', 'cooperative_type', 'website',
                  'manager_name', 'manager_email', 'manager_phone', 'manager_role', 'manager_bio',
                  'contact_name', 'contact_email', 'contact_phone', 'contact_role')
        read_only_fields = ('id', 'email', 'role', 'created_at', 'updated_at', 'is_approved')

class CooperativeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number', 'profile_picture', 
                  'address', 'city', 'province', 'postal_code', 'country', 
                  'registration_number', 'tax_id', 'year_established', 'cooperative_type', 'website',
                  'manager_name', 'manager_email', 'manager_phone', 'manager_role', 'manager_bio',
                  'contact_name', 'contact_email', 'contact_phone', 'contact_role',
                  'payment_details', 'is_approved')
        read_only_fields = ('id', 'email', 'is_approved')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token

class TokenVerifySerializer(serializers.Serializer):
    token = serializers.CharField()

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'role', 'is_approved')
        read_only_fields = fields

class CooperativeApprovalSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    is_approved = serializers.BooleanField()

class AdminLoginAsCooperativeSerializer(serializers.Serializer):
    cooperative_id = serializers.IntegerField()
    
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False)
