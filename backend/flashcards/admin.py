from django.contrib import admin
from .models import Flashcard, Tag, DailyCard, CardUsageLog, CardImage, ImageGenerationSettings


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin interface for Tag model."""
    
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    """Admin interface for Flashcard model."""
    
    list_display = ['title', 'phrase', 'version_number', 'is_live', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_live', 'is_active', 'created_at', 'tags']
    search_fields = ['title', 'phrase', 'definition', 'version_group']
    readonly_fields = ['created_at', 'updated_at', 'version_number', 'version_group', 'is_live']
    filter_horizontal = ['tags']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').prefetch_related('tags')


@admin.register(DailyCard)
class DailyCardAdmin(admin.ModelAdmin):
    """Admin interface for DailyCard model."""
    
    list_display = ['date', 'card', 'created_at']
    list_filter = ['date', 'created_at']
    readonly_fields = ['created_at']


@admin.register(CardUsageLog)
class CardUsageLogAdmin(admin.ModelAdmin):
    """Admin interface for CardUsageLog model."""
    
    list_display = ['card', 'used_date', 'cycle_number', 'created_at']
    list_filter = ['used_date', 'cycle_number', 'created_at']
    readonly_fields = ['created_at']


@admin.register(ImageGenerationSettings)
class ImageGenerationSettingsAdmin(admin.ModelAdmin):
    """Singleton: the global look and feel plus the bot's switches."""

    list_display = ['model', 'enabled', 'auto_generate_new_cards', 'max_attempts', 'updated_at']
    readonly_fields = ['updated_at', 'updated_by']

    def has_add_permission(self, request):
        # One row only; it is created on demand by ImageGenerationSettings.load().
        return not ImageGenerationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CardImage)
class CardImageAdmin(admin.ModelAdmin):
    """
    Read-mostly history of every generation.

    Prompts and images are editable only through the API and this screen, and
    the rows are append-only, so nothing here deletes history.
    """

    list_display = ['card_title', 'status', 'model', 'is_accepted', 'attempts', 'created_at']
    list_filter = ['status', 'is_accepted', 'is_auto', 'model', 'created_at']
    search_fields = ['card__title', 'version_group', 'prompt', 'error']
    readonly_fields = [
        'version_group', 'card', 'status', 'image', 'prompt', 'prompt_seed',
        'look_and_feel', 'look_and_feel_override', 'model', 'attempts', 'error',
        'cost_usd', 'provider_response_id', 'requested_by', 'is_auto',
        'created_at', 'updated_at', 'started_at', 'finished_at',
        'is_accepted', 'accepted_at', 'accepted_by',
    ]
    actions = ['accept_images', 'unaccept_images']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('card', 'requested_by', 'accepted_by')

    @admin.display(description='Card', ordering='card__title')
    def card_title(self, obj):
        return obj.card.title if obj.card else str(obj.version_group)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # History is append-only: an image that was shown to users stays on record.
        return False

    @admin.action(description='Accept selected image (one per card)')
    def accept_images(self, request, queryset):
        from .services import CardImageService

        accepted, skipped = 0, 0
        for image in queryset:
            try:
                CardImageService.accept(image, user=request.user)
                accepted += 1
            except ValueError:
                skipped += 1
        self.message_user(request, f'{accepted} accepted, {skipped} skipped (not generated successfully).')

    @admin.action(description='Withdraw selected images from public view')
    def unaccept_images(self, request, queryset):
        from .services import CardImageService

        count = 0
        for image in queryset.filter(is_accepted=True):
            CardImageService.unaccept(image)
            count += 1
        self.message_user(request, f'{count} image(s) withdrawn.')
