from django.contrib import admin
from .models import Card, CardVersion, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)


class CardVersionInline(admin.TabularInline):
    model = CardVersion
    extra = 0
    readonly_fields = ('created_at', 'version_number')
    ordering = ('-version_number',)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('title', 'phrase', 'created_by', 'enabled', 'views', 'created_at')
    list_filter = ('enabled', 'created_at', 'tags')
    search_fields = ('title', 'phrase', 'definition')
    ordering = ('-created_at',)
    readonly_fields = ('views', 'created_at', 'updated_at', 'deleted_at')
    filter_horizontal = ('tags',)
    inlines = [CardVersionInline]
    
    def get_queryset(self, request):
        """Include soft-deleted cards in admin"""
        return Card.objects.all()


@admin.register(CardVersion)
class CardVersionAdmin(admin.ModelAdmin):
    list_display = ('card', 'title', 'version_number', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('card__title', 'title', 'phrase', 'definition')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'version_number')
