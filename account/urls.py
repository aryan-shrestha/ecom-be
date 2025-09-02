from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from .views import UserListView, login_view, logout_view, user_profile, csrf_token_view

urlpatterns = [
    path('users/', UserListView.as_view(), name='user-list'),
]
