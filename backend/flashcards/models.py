from django.db import models
from django.contrib.auth import get_user_model

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
    """Main flashcard model."""
    
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
    
    # Version tracking
    version = models.PositiveIntegerField(default=1)
    parent_version = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='versions')

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} (v{self.version})"

    def get_current_version(self):
        """Get the current version of this card."""
        if self.parent_version:
            return self.parent_version.get_current_version()
        return self.versions.filter(is_active=True).order_by('-version').first() or self

    def create_new_version(self, **kwargs):
        """Create a new version of this card."""
        current = self.get_current_version()
        current.is_active = False
        current.save()
        
        # Create new version
        new_version = Flashcard.objects.create(
            title=kwargs.get('title', self.title),
            phrase=kwargs.get('phrase', self.phrase),
            definition=kwargs.get('definition', self.definition),
            front_image=kwargs.get('front_image', self.front_image),
            back_image=kwargs.get('back_image', self.back_image),
            created_by=kwargs.get('created_by', self.created_by),
            version=current.version + 1,
            parent_version=current.parent_version or current,
        )
        
        # Copy tags
        new_version.tags.set(kwargs.get('tags', self.tags.all()))
        
        return new_version


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
