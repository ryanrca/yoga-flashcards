"""
Tests for the users app views and API endpoints.
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from .factories import UserFactory

User = get_user_model()


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


@pytest.mark.django_db
class TestProfileUpdateSecurity:
    """Regression tests for self-service profile editing."""

    def test_user_cannot_escalate_own_role(self, api_client):
        """A user PUTting role=admin on their own profile is ignored."""
        user = UserFactory(role='user')
        api_client.force_authenticate(user=user)
        response = api_client.put('/api/users/profile/', {'role': 'admin'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.role == 'user'

    def test_user_cannot_reactivate_self(self, api_client):
        """is_active is not writable through the profile endpoint."""
        user = UserFactory(role='user', is_active=True)
        api_client.force_authenticate(user=user)
        api_client.put('/api/users/profile/', {'is_active': False}, format='json')
        user.refresh_from_db()
        assert user.is_active is True

    def test_user_can_update_own_names(self, api_client):
        """Ordinary profile fields still save."""
        user = UserFactory(role='user')
        api_client.force_authenticate(user=user)
        response = api_client.put(
            '/api/users/profile/',
            {'first_name': 'Ada', 'last_name': 'Lovelace'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == 'Ada'
        assert user.last_name == 'Lovelace'

    def test_user_can_set_daily_email_preference(self, api_client):
        """The email preference toggle persists."""
        user = UserFactory(role='user', daily_email_enabled=False)
        api_client.force_authenticate(user=user)
        response = api_client.put(
            '/api/users/profile/', {'daily_email_enabled': True}, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.daily_email_enabled is True


@pytest.mark.django_db
class TestChangePassword:
    """Tests for the change-password endpoint."""

    def test_change_password_success(self, api_client):
        user = UserFactory(role='user')
        user.set_password('oldpassword123')
        user.save()
        api_client.force_authenticate(user=user)
        response = api_client.post(
            '/api/users/change-password/',
            {'current_password': 'oldpassword123', 'new_password': 'brandnewpass456'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('brandnewpass456')

    def test_change_password_wrong_current(self, api_client):
        user = UserFactory(role='user')
        user.set_password('oldpassword123')
        user.save()
        api_client.force_authenticate(user=user)
        response = api_client.post(
            '/api/users/change-password/',
            {'current_password': 'wrongpassword', 'new_password': 'brandnewpass456'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.check_password('oldpassword123')

    def test_change_password_requires_auth(self, api_client):
        response = api_client.post(
            '/api/users/change-password/',
            {'current_password': 'x', 'new_password': 'brandnewpass456'},
            format='json',
        )
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


@pytest.mark.django_db
class TestUserManagementPermissions:
    """Every action on /api/users/manage/ is admin-only."""

    def test_regular_user_cannot_toggle_other_users(self, api_client):
        """toggle_active used to fall through to plain IsAuthenticated."""
        victim = UserFactory(role='user', is_active=True)
        attacker = UserFactory(role='user')
        api_client.force_authenticate(user=attacker)
        response = api_client.post(f'/api/users/manage/{victim.id}/toggle_active/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        victim.refresh_from_db()
        assert victim.is_active is True

    def test_regular_user_cannot_read_other_users(self, api_client):
        victim = UserFactory(role='user')
        attacker = UserFactory(role='user')
        api_client.force_authenticate(user=attacker)
        response = api_client.get(f'/api/users/manage/{victim.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_curator_cannot_read_user_stats(self, api_client):
        curator = UserFactory(role='curator')
        api_client.force_authenticate(user=curator)
        response = api_client.get('/api/users/manage/stats/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_without_is_staff_can_manage_users(self, api_client):
        """IsAdminOnly is role-based; DRF's IsAdminUser would 403 here."""
        admin = UserFactory(role='admin', is_staff=False, is_superuser=False)
        api_client.force_authenticate(user=admin)
        response = api_client.get('/api/users/manage/')
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_toggle_active(self, api_client):
        admin = UserFactory(role='admin', is_staff=False, is_superuser=False)
        victim = UserFactory(role='user', is_active=True)
        api_client.force_authenticate(user=admin)
        response = api_client.post(f'/api/users/manage/{victim.id}/toggle_active/')
        assert response.status_code == status.HTTP_200_OK
        victim.refresh_from_db()
        assert victim.is_active is False


@pytest.mark.django_db
class TestDeleteAccount:
    """Tests for self-service account deletion."""

    def test_delete_account_soft_deletes(self, api_client):
        user = UserFactory(role='user')
        api_client.force_authenticate(user=user)
        response = api_client.delete('/api/users/delete-account/')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_deleted is True
        assert user.is_active is False

    def test_delete_account_requires_auth(self, api_client):
        response = api_client.delete('/api/users/delete-account/')
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_deleted_user_cannot_log_in(self, api_client):
        user = UserFactory(role='user')
        user.set_password('correcthorse123')
        user.save()
        user.soft_delete()
        response = api_client.post(
            '/api/users/login/',
            {'email': user.email, 'password': 'correcthorse123'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deleted_user_session_is_dead(self, api_client):
        """An existing session stops resolving once the account is deleted."""
        user = UserFactory(role='user')
        user.set_password('correcthorse123')
        user.save()
        assert api_client.login(username=user.username, password='correcthorse123')
        assert api_client.get('/api/users/auth-status/').data['authenticated'] is True
        user.soft_delete()
        assert api_client.get('/api/users/auth-status/').data['authenticated'] is False

    def test_cannot_register_over_a_deleted_account(self, api_client):
        user = UserFactory(role='user', email='gone@example.com')
        user.soft_delete()
        response = api_client.post(
            '/api/users/register/',
            {
                'email': 'gone@example.com',
                'password': 'securepass123',
                'password_confirm': 'securepass123',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDeletedUserVisibility:
    """Deleted accounts are hidden from listings but reachable by admins."""

    def test_deleted_users_hidden_from_list_by_default(self, api_client):
        admin = UserFactory(role='admin')
        gone = UserFactory(role='user')
        gone.soft_delete()
        api_client.force_authenticate(user=admin)
        response = api_client.get('/api/users/manage/')
        ids = [u['id'] for u in response.data['results']]
        assert gone.id not in ids
        assert admin.id in ids

    def test_admin_can_list_deleted_users(self, api_client):
        admin = UserFactory(role='admin')
        gone = UserFactory(role='user')
        gone.soft_delete()
        api_client.force_authenticate(user=admin)
        response = api_client.get('/api/users/manage/?include_deleted=true')
        ids = [u['id'] for u in response.data['results']]
        assert gone.id in ids

    def test_admin_can_retrieve_a_deleted_user(self, api_client):
        admin = UserFactory(role='admin')
        gone = UserFactory(role='user')
        gone.soft_delete()
        api_client.force_authenticate(user=admin)
        response = api_client.get(f'/api/users/manage/{gone.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_deleted'] is True

    def test_non_admin_cannot_list_users_at_all(self, api_client):
        user = UserFactory(role='user')
        api_client.force_authenticate(user=user)
        assert api_client.get('/api/users/manage/').status_code == status.HTTP_403_FORBIDDEN

    def test_stats_exclude_deleted_users(self, api_client):
        admin = UserFactory(role='admin')
        gone = UserFactory(role='user')
        gone.soft_delete()
        api_client.force_authenticate(user=admin)
        response = api_client.get('/api/users/manage/stats/')
        assert response.data['deleted'] == 1
        assert response.data['total'] == User.objects.filter(is_deleted=False).count()


@pytest.mark.django_db
class TestAdminUserDeletion:
    """Admin deletion is a soft delete, and is reversible."""

    def test_admin_delete_soft_deletes(self, api_client):
        admin = UserFactory(role='admin')
        victim = UserFactory(role='curator')
        api_client.force_authenticate(user=admin)
        response = api_client.delete(f'/api/users/manage/{victim.id}/')
        assert response.status_code == status.HTTP_200_OK
        victim.refresh_from_db()
        assert victim.is_deleted is True
        assert User.objects.filter(pk=victim.pk).exists()

    def test_admin_cannot_delete_themselves_here(self, api_client):
        admin = UserFactory(role='admin')
        api_client.force_authenticate(user=admin)
        response = api_client.delete(f'/api/users/manage/{admin.id}/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        admin.refresh_from_db()
        assert admin.is_deleted is False

    def test_admin_can_restore(self, api_client):
        admin = UserFactory(role='admin')
        victim = UserFactory(role='user')
        victim.soft_delete()
        api_client.force_authenticate(user=admin)
        response = api_client.post(f'/api/users/manage/{victim.id}/restore/')
        assert response.status_code == status.HTTP_200_OK
        victim.refresh_from_db()
        assert victim.is_deleted is False
        assert victim.is_active is True

    def test_restore_rejects_a_live_user(self, api_client):
        admin = UserFactory(role='admin')
        other = UserFactory(role='user')
        api_client.force_authenticate(user=admin)
        response = api_client.post(f'/api/users/manage/{other.id}/restore/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_toggle_active_refuses_deleted_user(self, api_client):
        """Otherwise toggle_active would quietly resurrect a deleted account."""
        admin = UserFactory(role='admin')
        gone = UserFactory(role='user')
        gone.soft_delete()
        api_client.force_authenticate(user=admin)
        response = api_client.post(f'/api/users/manage/{gone.id}/toggle_active/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        gone.refresh_from_db()
        assert gone.is_active is False


@pytest.mark.django_db
class TestCsrfEnforcement:
    """
    CSRF is enforced on authenticated API writes.

    These use APIClient(enforce_csrf_checks=True); the default test client sets
    _dont_enforce_csrf_checks, which is exactly what the old
    DisableCSRFMiddleware did for every real request.
    """

    def _logged_in_client(self, password='correcthorse123'):
        from rest_framework.test import APIClient

        user = UserFactory(role='curator')
        user.set_password(password)
        user.save()
        client = APIClient(enforce_csrf_checks=True)
        assert client.login(username=user.username, password=password)
        return client, user

    def test_csrf_endpoint_sets_the_cookie(self):
        from rest_framework.test import APIClient

        client = APIClient(enforce_csrf_checks=True)
        response = client.get('/api/users/csrf/')
        assert response.status_code == status.HTTP_200_OK
        assert 'csrftoken' in response.cookies
        assert response.data['csrfToken']

    def test_auth_status_sets_the_cookie(self):
        """The router guard hits this on boot, so a session gets a token early."""
        from rest_framework.test import APIClient

        client = APIClient(enforce_csrf_checks=True)
        response = client.get('/api/users/auth-status/')
        assert response.status_code == status.HTTP_200_OK
        assert 'csrftoken' in response.cookies

    def test_write_without_csrf_token_is_rejected(self):
        client, _ = self._logged_in_client()
        response = client.post('/api/tags/', {'name': 'Forged'}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_write_with_csrf_token_succeeds(self):
        client, _ = self._logged_in_client()
        client.get('/api/users/csrf/')
        token = client.cookies['csrftoken'].value
        response = client.post(
            '/api/tags/', {'name': 'Legitimate'}, format='json', HTTP_X_CSRFTOKEN=token
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_read_does_not_need_a_token(self):
        client, _ = self._logged_in_client()
        assert client.get('/api/cards/').status_code == status.HTTP_200_OK

    def test_public_read_still_works(self):
        from rest_framework.test import APIClient

        client = APIClient(enforce_csrf_checks=True)
        assert client.get('/api/tags/').status_code == status.HTTP_200_OK
        assert client.get('/api/health/').status_code == status.HTTP_200_OK
