from django.contrib.auth import login, logout, update_session_auth_hash
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from rest_framework import status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .serializers import (
    UserRegistrationSerializer, LoginSerializer, UserSerializer, AdminUserSerializer,
    ChangePasswordSerializer, ProfileUpdateSerializer,
)
from .services import UserService
from flashcards.permissions import IsAdminOnly
from .models import User


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user."""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        UserService.send_verification_email(user)
        return Response({
            'message': 'User created successfully. Please check your email to verify your account.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login user."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout user."""
    logout(request)
    return Response({'message': 'Logout successful'})


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request):
    """Hand out a CSRF token and set the csrftoken cookie.

    DRF views are csrf_exempt, so CsrfViewMiddleware never runs for /api/ paths
    and Django never sets the cookie by itself. The frontend calls this before
    its first unsafe request; the token is also returned in the body for clients
    that cannot read cookies.
    """
    return Response({'csrfToken': get_token(request)})


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def auth_status(request):
    """Check authentication status.

    Carries ensure_csrf_cookie because the router guard calls this on first
    navigation, so a browsing session normally has a token before it needs one.
    """
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'user': UserSerializer(request.user).data
        })
    return Response({'authenticated': False})


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get or update user profile."""
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """Delete the logged-in user's own account.

    This is a soft delete: the row, the user's profile and every card they
    authored are left untouched. The account is simply disabled, so it can no
    longer log in and stops appearing in user listings. Only an admin can still
    see it, via /api/users/manage/?include_deleted=true or the Django admin.
    """
    user = request.user
    user.soft_delete()
    logout(request)
    return Response({'message': 'Account deleted'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the logged-in user's password."""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.save()
        # Keep the current session valid after the password hash changes.
        update_session_auth_hash(request, user)
        return Response({'message': 'Password changed successfully'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users (admin only).
    Provides CRUD operations for user management.

    Every action is admin-only, including the extra `retrieve`, `stats` and
    `toggle_active` actions. IsAdminOnly checks role == 'admin' or
    is_superuser; DRF's IsAdminUser checks is_staff instead and would lock
    out a role='admin' user who is not staff.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email', 'last_login']
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        # Soft-deleted accounts are hidden unless explicitly requested. Detail
        # routes never filter them out, so an admin can always reach one by id
        # to inspect or restore it.
        if self.action == 'list':
            include_deleted = self.request.query_params.get('include_deleted', '')
            if include_deleted.lower() not in ('true', '1', 'yes'):
                queryset = queryset.filter(is_deleted=False)

        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return AdminUserSerializer
        return UserSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete: disable the account, keep the row and its cards."""
        user = self.get_object()
        if user == request.user:
            return Response(
                {'error': 'Use /api/users/delete-account/ to delete your own account'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.soft_delete()
        return Response({
            'message': 'User deleted',
            'user': UserSerializer(user).data,
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Undo a soft delete and re-enable the account."""
        user = self.get_object()
        if not user.is_deleted:
            return Response(
                {'error': 'User is not deleted'}, status=status.HTTP_400_BAD_REQUEST
            )
        user.restore()
        return Response({
            'message': 'User restored',
            'user': UserSerializer(user).data,
        })

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle user active status."""
        user = self.get_object()
        if user.is_deleted:
            # Otherwise this would quietly resurrect a deleted account.
            return Response(
                {'error': 'Restore the account before changing its active status'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = not user.is_active
        user.save()
        return Response({
            'message': f"User {'activated' if user.is_active else 'deactivated'} successfully",
            'user': UserSerializer(user).data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics. Deleted accounts are excluded from every count."""
        live_users = User.objects.filter(is_deleted=False)
        return Response({
            'total': live_users.count(),
            'active': live_users.filter(is_active=True).count(),
            'admins': live_users.filter(role='admin').count(),
            'deleted': User.objects.filter(is_deleted=True).count(),
        })
