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
    short_answer = models.TextField(blank=True, null=True, help_text="Brief answer or key points")
    front_image = models.ImageField(upload_to='flashcard_images/', blank=True, null=True)
    back_image = models.ImageField(upload_to='flashcard_images/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='flashcards')
    
    # Metadata
    # PROTECT, not CASCADE: deleting a user must never take their card library
    # (and its version history) with it. Accounts are soft deleted instead --
    # see User.soft_delete().
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_cards')
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
            short_answer=kwargs.get('short_answer', self.short_answer),
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
            short_answer=self.short_answer,
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


class ImageGenerationSettings(models.Model):
    """
    Singleton holding the global image-generation configuration.

    There is exactly one row (pk=1). `load()` creates it on first access so the
    admin screen never has to deal with a missing record.
    """

    DEFAULT_MODEL = 'black-forest-labs/flux.2-pro'
    DEFAULT_LOOK_AND_FEEL = (
        'Serene minimalist illustration, soft natural light, warm muted earth tones, '
        'hand-painted texture, calm and contemplative mood, generous negative space.'
    )

    look_and_feel = models.TextField(
        default=DEFAULT_LOOK_AND_FEEL,
        blank=True,
        help_text="Style guidance appended to every prompt. Overridable per image.",
    )
    model = models.CharField(
        max_length=200,
        default=DEFAULT_MODEL,
        help_text="OpenRouter model slug used for new generations.",
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Master switch. When off, the bot generates nothing.",
    )
    auto_generate_new_cards = models.BooleanField(
        default=True,
        help_text="Queue an image automatically the first time a card is seen.",
    )
    max_attempts = models.PositiveSmallIntegerField(
        default=3,
        help_text="Hard cap on generation attempts per image row, so a failing card cannot loop forever.",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )

    class Meta:
        verbose_name = 'Image generation settings'
        verbose_name_plural = 'Image generation settings'

    def __str__(self):
        return f"Image generation settings ({self.model}, {'on' if self.enabled else 'off'})"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # The singleton is configuration, not data; deleting it would break the
        # admin screen and the bot.
        raise NotImplementedError('The image generation settings row cannot be deleted.')

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class CardImage(models.Model):
    """
    One AI image generation for a card, plus the prompt that produced it.

    Rows are append-only history: regenerating creates a new row and never
    edits or deletes an old one.

    Attached to `version_group` rather than a Flashcard id because editing a
    card creates a brand new Flashcard row (see Flashcard.create_new_version).
    Keying on the id would orphan every image the moment a curator fixed a typo.
    """

    QUEUED = 'queued'
    GENERATING = 'generating'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    STATUS_CHOICES = [
        (QUEUED, 'Queued'),
        (GENERATING, 'Generating'),
        (SUCCEEDED, 'Succeeded'),
        (FAILED, 'Failed'),
    ]

    version_group = models.UUIDField(
        db_index=True,
        help_text="The card family this image belongs to; survives card edits.",
    )
    card = models.ForeignKey(
        Flashcard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_images',
        help_text="The card version whose text seeded the prompt. Kept for provenance only.",
    )

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=QUEUED, db_index=True)
    image = models.ImageField(upload_to='card_images/generated/', blank=True, null=True)

    prompt = models.TextField(help_text="The full prompt sent to the model, look and feel included.")
    prompt_seed = models.TextField(
        blank=True,
        help_text="The card-derived portion of the prompt, before style guidance.",
    )
    look_and_feel = models.TextField(
        blank=True,
        help_text="The style guidance actually used, snapshotted at generation time.",
    )
    look_and_feel_override = models.TextField(
        blank=True,
        help_text="Per-image style guidance. When set, it replaces the global look and feel.",
    )
    model = models.CharField(max_length=200)

    is_accepted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Only an accepted image is visible outside the admin area.",
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )

    attempts = models.PositiveSmallIntegerField(default=0)
    error = models.TextField(blank=True)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    provider_response_id = models.CharField(max_length=200, blank=True)

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_card_images',
        help_text="Null when the bot queued it automatically.",
    )
    is_auto = models.BooleanField(
        default=False,
        help_text="True when queued by the bot rather than by an admin.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['version_group', '-created_at']),
            models.Index(fields=['version_group', 'is_accepted']),
            models.Index(fields=['status', 'created_at']),
        ]
        # Deliberately no partial UniqueConstraint on (version_group, is_accepted):
        # MySQL has no partial indexes, so Django would silently skip it and the
        # guarantee would exist in tests (SQLite) but not in production.
        # CardImageService.accept() enforces single-accepted inside a transaction.

    def __str__(self):
        return f"{self.version_group} {self.model} ({self.status})"

    @property
    def effective_look_and_feel(self):
        """Per-image override wins over the global setting."""
        if self.look_and_feel_override.strip():
            return self.look_and_feel_override.strip()
        return ImageGenerationSettings.load().look_and_feel.strip()
