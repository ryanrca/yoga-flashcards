from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Tag(models.Model):
    """Tag model for organizing flashcards."""
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Flashcard(models.Model):
    """Main flashcard model with versioning support."""
    
    title = models.CharField(max_length=200)
    phrase = models.CharField(max_length=500, blank=True, null=True, help_text="Sanskrit phrase or term")
    definition = models.TextField(help_text="English definition or description")
    front_image = models.ImageField(upload_to='flashcard_images/', blank=True, null=True)
    back_image = models.ImageField(upload_to='flashcard_images/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='flashcards')
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_cards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Version tracking - all versions of same card share version_group
    version_group = models.UUIDField(default=uuid.uuid4, db_index=True, help_text="Groups all versions of the same card")
    version_number = models.PositiveIntegerField(default=1)
    is_live = models.BooleanField(default=True, db_index=True, help_text="Only one version per group should be live")

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['version_group', 'is_live']),
            models.Index(fields=['version_group', '-version_number']),
        ]

    def __str__(self):
        status = "LIVE" if self.is_live else f"v{self.version_number}"
        return f"{self.title} ({status})"

    def get_version_history(self):
        """Get all versions of this card ordered by version number descending."""
        return Flashcard.objects.filter(
            version_group=self.version_group
        ).order_by('-version_number')

    def create_new_version(self, updated_by, **kwargs):
        """Create a new version of this card and mark it as live."""
        # Get current live version
        current_live = Flashcard.objects.filter(
            version_group=self.version_group,
            is_live=True
        ).first()
        
        # Mark current live version as not live
        if current_live:
            current_live.is_live = False
            current_live.save()
            next_version = current_live.version_number + 1
        else:
            next_version = 1
        
        # Create new version
        new_version = Flashcard.objects.create(
            title=kwargs.get('title', self.title),
            phrase=kwargs.get('phrase', self.phrase),
            definition=kwargs.get('definition', self.definition),
            front_image=kwargs.get('front_image', self.front_image),
            back_image=kwargs.get('back_image', self.back_image),
            created_by=updated_by,
            version_group=self.version_group,
            version_number=next_version,
            is_live=True,
            is_active=True,
        )
        
        # Copy tags if not provided
        if 'tags' in kwargs and kwargs['tags'] is not None:
            new_version.tags.set(kwargs['tags'])
        else:
            new_version.tags.set(self.tags.all())
        
        return new_version

    def revert_to_this_version(self, reverted_by):
        """Create a new live version by copying this version's data."""
        return self.create_new_version(
            updated_by=reverted_by,
            title=self.title,
            phrase=self.phrase,
            definition=self.definition,
            front_image=self.front_image,
            back_image=self.back_image,
            tags=list(self.tags.all()),
        )


class DailyCard(models.Model):
    """Model to track daily card selection."""
    
    card = models.ForeignKey(Flashcard, on_delete=models.CASCADE)
    date = models.DateField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Daily card for {self.date}: {self.card.title}"


class CardUsageLog(models.Model):
    """Log to track which cards have been used as daily cards."""
    
    card = models.ForeignKey(Flashcard, on_delete=models.CASCADE)
    used_date = models.DateField()
    cycle_number = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_date']
        unique_together = ['card', 'used_date', 'cycle_number']

    def __str__(self):
        return f"{self.card.title} used on {self.used_date} (cycle {self.cycle_number})"
