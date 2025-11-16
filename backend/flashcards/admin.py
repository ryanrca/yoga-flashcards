from django.contrib import admin
from .models import Flashcard, Tag, DailyCard, CardUsageLog


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
