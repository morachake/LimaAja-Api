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
                  'profile_picture', 'address', 'city', 'country')
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
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number', 'role', 'profile_picture', 
                  'address', 'city', 'country', 'created_at', 'updated_at')
        read_only_fields = ('id', 'email', 'role', 'created_at', 'updated_at')

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls,user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token
class TokenVerifySerializer(serializers.Serializer):
    token = serializers.CharField()

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta :
        model = User
        fields = ('id','email','full_name','role')
        read_only_fields = fields
