from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserListView, CustomUserViewSet, user_profile,
    user_dashboard, CustomTokenObtainPairView
)

# Create router for the custom user viewset
router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='customuser')

urlpatterns = [
    path('users/', UserListView.as_view(), name='user-list'),
    # Include custom user routes (for additional endpoints like profile_stats)
    path('custom/', include(router.urls)),
    # Alternative custom profile endpoints
    path('profile/', user_profile, name='user-profile'),
    path('dashboard/', user_dashboard, name='user-dashboard'),
    # Custom JWT token endpoint for email login
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]
