# views.py
from rest_framework import generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from djoser.views import UserViewSet as DjoserUserViewSet

from django.contrib.auth import get_user_model
from .serializers import UserSerializer, CustomUserSerializer, CustomTokenObtainPairSerializer


class UserListView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view that uses email or username for authentication
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserListView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class CustomUserViewSet(DjoserUserViewSet):
    """
    Custom UserViewSet that extends Djoser's UserViewSet
    Customizes the /users/me/ endpoint behavior
    """

    def get_serializer_class(self):
        """Use custom serializer for 'me' action"""
        if self.action == 'me':
            return CustomUserSerializer
        return super().get_serializer_class()

    @action(['get', 'put', 'patch'], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """
        Custom implementation of users/me endpoint
        Adds additional functionality beyond Djoser's default
        """
        self.get_object = self.get_instance

        if request.method == 'GET':
            return self.retrieve(request, *args, **kwargs)
        elif request.method == 'PUT':
            return self.update(request, *args, **kwargs)
        elif request.method == 'PATCH':
            return self.partial_update(request, *args, **kwargs)

    @action(['post'], detail=False, permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Custom endpoint for changing password
        Available at /auth/users/change_password/
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {'message': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )

    @action(['get'], detail=False, permission_classes=[IsAuthenticated])
    def profile_stats(self, request):
        """
        Custom endpoint for user profile statistics
        Available at /auth/users/profile_stats/
        """
        user = request.user

        # Add your custom statistics here
        stats = {
            'total_orders': 0,  # You can integrate with orders app
            'member_since': user.date_joined,
            'last_login': user.last_login,
            'is_verified': user.is_active,
        }

        return Response(stats, status=status.HTTP_200_OK)


# Alternative: Completely custom profile endpoints
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Custom user profile endpoint as an alternative to Djoser's users/me
    Available at /accounts/profile/
    """
    user = request.user

    if request.method == 'GET':
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = CustomUserSerializer(
            user, data=request.data, partial=partial)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """
    Custom user dashboard with comprehensive user information
    Available at /accounts/dashboard/
    """
    user = request.user

    # You can add relationships to other models here
    dashboard_data = {
        'user': CustomUserSerializer(user).data,
        'account_status': {
            'is_active': user.is_active,
            'is_verified': user.is_active,  # You can add email verification logic
            'member_since': user.date_joined,
            'last_login': user.last_login,
        },
        'activity': {
            'total_orders': 0,  # Integrate with orders app
            'cart_items': 0,    # Integrate with cart app
        }
    }

    return Response(dashboard_data)
