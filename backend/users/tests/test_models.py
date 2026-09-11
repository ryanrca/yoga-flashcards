"""
Tests for the users app models.
"""
import pytest
from django.contrib.auth import get_user_model
from .factories import UserFactory, AdminUserFactory, CuratorUserFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self):
        """Test creating a basic user."""
        user = UserFactory()
        assert user.pk is not None
        assert user.role == 'user'
        assert user.is_active is True
        assert user.is_staff is False

    def test_create_admin_user(self):
        """Test creating an admin user."""
        admin = AdminUserFactory()
        assert admin.role == 'admin'
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_create_curator_user(self):
        """Test creating a curator user."""
        curator = CuratorUserFactory()
        assert curator.role == 'curator'
        assert curator.is_staff is False

    def test_user_str(self):
        """Test user string representation."""
        user = UserFactory(username='testuser')
        assert str(user) == 'testuser'

    def test_is_admin_method(self):
        """Test is_admin() method."""
        user = UserFactory(role='user')
        admin = UserFactory(role='admin')
        superuser = UserFactory(role='user', is_superuser=True)

        assert user.is_admin() is False
        assert admin.is_admin() is True
        assert superuser.is_admin() is True

    def test_is_curator_method(self):
        """Test is_curator() method."""
        user = UserFactory(role='user')
        curator = UserFactory(role='curator')
        admin = UserFactory(role='admin')
        superuser = UserFactory(role='user', is_superuser=True)

        assert user.is_curator() is False
        assert curator.is_curator() is True
        assert admin.is_curator() is True
        assert superuser.is_curator() is True

    def test_can_edit_cards_method(self):
        """Test can_edit_cards() method."""
        user = UserFactory(role='user')
        curator = UserFactory(role='curator')
        admin = UserFactory(role='admin')

        assert user.can_edit_cards() is False
        assert curator.can_edit_cards() is True
        assert admin.can_edit_cards() is True

    def test_can_edit_users_method(self):
        """Test can_edit_users() method."""
        user = UserFactory(role='user')
        curator = UserFactory(role='curator')
        admin = UserFactory(role='admin')

        assert user.can_edit_users() is False
        assert curator.can_edit_users() is False
        assert admin.can_edit_users() is True

    def test_user_username_unique(self):
        """Test that username must be unique."""
        UserFactory(username='uniqueuser')
        with pytest.raises(Exception):
            UserFactory(username='uniqueuser')

    def test_user_default_role(self):
        """Test that default role is 'user'."""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        assert user.role == 'user'

    def test_daily_email_enabled_default(self):
        """Test daily_email_enabled defaults to False."""
        user = UserFactory()
        assert user.daily_email_enabled is False

    def test_email_verified_default(self):
        """Test email_verified defaults to False."""
        user = UserFactory()
        assert user.email_verified is False


@pytest.mark.django_db
class TestSoftDelete:
    """Tests for account soft deletion."""

    def test_soft_delete_sets_flags(self):
        user = UserFactory(role='user', is_active=True)
        user.soft_delete()
        user.refresh_from_db()
        assert user.is_deleted is True
        assert user.is_active is False
        assert user.deleted_at is not None

    def test_soft_delete_keeps_the_row(self):
        user = UserFactory(role='user')
        pk = user.pk
        user.soft_delete()
        assert User.objects.filter(pk=pk).exists()

    def test_soft_delete_keeps_authored_cards(self):
        """The whole point: a deleted curator's card library survives."""
        from flashcards.models import Flashcard
        from flashcards.tests.factories import FlashcardFactory

        curator = UserFactory(role='curator')
        card = FlashcardFactory(created_by=curator)
        curator.soft_delete()
        card.refresh_from_db()
        assert Flashcard.objects.filter(pk=card.pk).exists()
        assert card.created_by_id == curator.pk

    def test_soft_delete_is_idempotent(self):
        user = UserFactory(role='user')
        user.soft_delete()
        first = user.deleted_at
        user.soft_delete()
        user.refresh_from_db()
        assert user.deleted_at == first

    def test_restore_reenables_account(self):
        user = UserFactory(role='user')
        user.soft_delete()
        user.restore()
        user.refresh_from_db()
        assert user.is_deleted is False
        assert user.is_active is True
        assert user.deleted_at is None

    def test_hard_delete_is_blocked_while_cards_exist(self):
        """PROTECT on created_by stops a cascade from wiping a card library."""
        from django.db.models import ProtectedError
        from flashcards.tests.factories import FlashcardFactory

        curator = UserFactory(role='curator')
        FlashcardFactory(created_by=curator)
        with pytest.raises(ProtectedError):
            curator.delete()
