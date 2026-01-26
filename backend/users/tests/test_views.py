"""
Tests for the users app views and API endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from .factories import UserFactory


@pytest.mark.django_db
class TestRegistration:
    """Tests for user registration endpoint."""

    def test_register_success(self, api_client):
        """Test successful user registration."""
        data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = api_client.post('/api/users/register/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'

    def test_register_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match."""
        data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'differentpass',
        }
        response = api_client.post('/api/users/register/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_username(self, api_client):
        """Test registration generates unique username for duplicate emails."""
        # First registration creates user with username derived from email
        data1 = {
            'email': 'test@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        }
        response1 = api_client.post('/api/users/register/', data1)
        assert response1.status_code == status.HTTP_201_CREATED

        # Second registration with different email but same base username
        data2 = {
            'email': 'test@different.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        }
        response2 = api_client.post('/api/users/register/', data2)
        assert response2.status_code == status.HTTP_201_CREATED
        # Should have different usernames
        assert response1.data['user']['username'] != response2.data['user']['username']

    def test_register_missing_fields(self, api_client):
        """Test registration fails without required fields."""
        # Missing password_confirm
        data = {
            'email': 'test@example.com',
            'password': 'securepass123',
        }
        response = api_client.post('/api/users/register/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, api_client):
        """Test successful login."""
        user = UserFactory(email='test@example.com')
        user.set_password('testpass123')
        user.save()

        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post('/api/users/login/', data)
        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data

    def test_login_invalid_password(self, api_client):
        """Test login fails with wrong password."""
        user = UserFactory(email='test@example.com')
        user.set_password('testpass123')
        user.save()

        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = api_client.post('/api/users/login/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, api_client):
        """Test login fails with nonexistent email."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = api_client.post('/api/users/login/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client):
        """Test login fails for inactive user."""
        user = UserFactory(email='inactive@example.com', is_active=False)
        user.set_password('testpass123')
        user.save()

        data = {
            'email': 'inactive@example.com',
            'password': 'testpass123'
        }
        response = api_client.post('/api/users/login/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogout:
    """Tests for user logout endpoint."""

    def test_logout_success(self, authenticated_client):
        """Test successful logout."""
        response = authenticated_client.post('/api/users/logout/')
        assert response.status_code == status.HTTP_200_OK

    def test_logout_unauthenticated(self, api_client):
        """Test logout requires authentication."""
        response = api_client.post('/api/users/logout/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAuthStatus:
    """Tests for auth status endpoint."""

    def test_auth_status_authenticated(self, authenticated_client, user):
        """Test auth status when authenticated."""
        response = authenticated_client.get('/api/users/auth-status/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['authenticated'] is True
        assert response.data['user']['email'] == user.email

    def test_auth_status_unauthenticated(self, api_client):
        """Test auth status when not authenticated."""
        response = api_client.get('/api/users/auth-status/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['authenticated'] is False


@pytest.mark.django_db
class TestProfile:
    """Tests for user profile endpoint."""

    def test_get_profile(self, authenticated_client, user):
        """Test getting user profile."""
        response = authenticated_client.get('/api/users/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_get_profile_unauthenticated(self, api_client):
        """Test profile requires authentication."""
        response = api_client.get('/api/users/profile/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_profile(self, authenticated_client, user):
        """Test updating user profile."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = authenticated_client.put('/api/users/profile/', data)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'


@pytest.mark.django_db
class TestUserManagement:
    """Tests for admin user management endpoints."""

    def test_list_users_as_admin(self, admin_client):
        """Test admin can list all users."""
        UserFactory.create_batch(3)
        response = admin_client.get('/api/users/manage/')
        assert response.status_code == status.HTTP_200_OK
        # At least 3 users created + admin user
        assert len(response.data['results']) >= 3

    def test_list_users_as_curator_forbidden(self, curator_client):
        """Test curator cannot list users."""
        response = curator_client.get('/api/users/manage/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_as_user_forbidden(self, authenticated_client):
        """Test regular user cannot list users."""
        response = authenticated_client.get('/api/users/manage/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_users_by_role(self, admin_client):
        """Test filtering users by role."""
        UserFactory(role='curator')
        UserFactory(role='curator')
        UserFactory(role='user')

        response = admin_client.get('/api/users/manage/?role=curator')
        assert response.status_code == status.HTTP_200_OK
        for user in response.data['results']:
            assert user['role'] == 'curator'

    def test_toggle_user_active(self, admin_client):
        """Test toggling user active status."""
        user = UserFactory(is_active=True)
        response = admin_client.post(f'/api/users/manage/{user.id}/toggle_active/')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is False

    def test_user_stats(self, admin_client):
        """Test getting user statistics."""
        UserFactory.create_batch(3, role='user')
        UserFactory(role='admin')

        response = admin_client.get('/api/users/manage/stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert 'active' in response.data
        assert 'admins' in response.data
