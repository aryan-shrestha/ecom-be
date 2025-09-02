# views.py

from django.middleware.csrf import get_token
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from .serializers import UserSerializer, LoginSerializer


class UserListView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


# views.py


class UserListView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
