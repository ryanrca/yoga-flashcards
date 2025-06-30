import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def card_image_upload_path(instance, filename):
    """Generate upload path for card images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('cards', filename)


class Tag(models.Model):
    """Tag model for categorizing flashcards"""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Card(models.Model):
    """Main flashcard model"""
    title = models.CharField(max_length=200)
    phrase = models.TextField()
    definition = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    views = models.PositiveIntegerField(default=0)
    enabled = models.BooleanField(default=True)
    front_photo = models.ImageField(upload_to=card_image_upload_path, null=True, blank=True)
    back_photo = models.ImageField(upload_to=card_image_upload_path, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='cards')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def soft_delete(self):
        """Soft delete the card"""
        self.deleted_at = timezone.now()
        self.save()

    def is_deleted(self):
        """Check if card is soft deleted"""
        return self.deleted_at is not None

    def increment_views(self):
        """Increment view counter"""
        self.views += 1
        self.save(update_fields=['views'])


class CardVersion(models.Model):
    """Version history for cards"""
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='versions')
    title = models.CharField(max_length=200)
    phrase = models.TextField()
    definition = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    version_number = models.PositiveIntegerField()

    class Meta:
        ordering = ['-version_number']
        unique_together = ['card', 'version_number']

    def __str__(self):
        return f"{self.card.title} - v{self.version_number}"
