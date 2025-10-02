# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email',
                  'first_name', 'last_name', 'date_joined']


class CustomUserSerializer(DjoserUserSerializer):
    """
    Custom serializer for users/me endpoint
    Extends Djoser's UserSerializer with additional fields or custom logic
    """
    full_name = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + \
            ('id', 'full_name', 'username', 'is_staff', 'is_superuser', 'is_active',)

    def get_full_name(self, obj):
        """Return user's full name"""
        first_name: str = obj.first_name or ""
        last_name: str = obj.last_name or ""
        full_name = f"{first_name.capitalize()} {last_name.capitalize()}".strip()

        return full_name


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """
    Custom serializer for user creation with additional validation
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'password', 'password_confirm']

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that allows login with email only
    """
    username_field = 'email'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.EmailField()
        self.fields['password'] = serializers.CharField()

        # Remove the default username field
        if 'username' in self.fields:
            del self.fields['username']

    def validate(self, attrs):
        email = attrs.get(self.username_field)
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,  # Pass email as username to the backend
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'No active account found with the given email and password'
                )

            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')

            refresh = self.get_token(user)

            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".'
            )


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login - supports email only
    """
    email = serializers.EmailField(
        help_text="Email address"
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
