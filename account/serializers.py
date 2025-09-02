# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email',
                  'first_name', 'last_name', 'date_joined']


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    username = serializers.CharField(
        max_length=150,
        help_text="Username or email address"
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
