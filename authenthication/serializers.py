from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,required=True,validators=[validate_password])
    password2 = serializers.CharField(write_only=True,required=True)
    
    class Meta:
        model = User
        fields = ('id','full_name','email','phone_number','password','password2','role','profile_picture','adress','city','country')
        extra_kwargs = {
            'full_name': {'required' : True},
            'email' : {'required': True},
            'phone_number':{'required': True},
            'role' : {'required': True}
        }
    def validate(self,attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password Fields Don't match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128,write_only=True)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
class UserProfileSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ('id','full_name','email','phone_number','role','profile_picture','adress','city','country','created_at','updated_at')
        read_only_fields = ('id','role','created_at','updated_at')