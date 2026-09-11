from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Extended user model with additional fields."""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('curator', 'Curator'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    daily_email_enabled = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete. Accounts are never removed from the database: deleting one
    # only disables it, so the cards the user authored and the version history
    # that references them stay intact.
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Account has been deleted. The row is kept; the account cannot be used.",
    )
    deleted_at = models.DateTimeField(blank=True, null=True)

    def soft_delete(self):
        """Disable the account without removing any rows.

        Also clears is_active, which is what actually blocks login: both
        Django's ModelBackend and LoginSerializer reject inactive users.
        """
        if self.is_deleted:
            return
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        # updated_at is auto_now, so it has to be listed to be written.
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active', 'updated_at'])

    def restore(self):
        """Undo a soft delete and re-enable the account."""
        if not self.is_deleted:
            return
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active', 'updated_at'])

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def is_curator(self):
        return self.role in ['curator', 'admin'] or self.is_superuser

    def can_edit_cards(self):
        return self.is_curator()

    def can_edit_users(self):
        return self.is_admin()


class UserProfile(models.Model):
    """Extended profile information for users."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    favorite_cards = models.ManyToManyField('flashcards.Flashcard', blank=True, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
