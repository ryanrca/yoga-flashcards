from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = ['username', 'email', 'role', 'email_verified', 'is_active', 'is_deleted', 'date_joined']
    list_filter = ['role', 'email_verified', 'is_active', 'is_deleted', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['deleted_at']
    actions = ['soft_delete_users', 'restore_users']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'daily_email_enabled', 'email_verified')
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at'),
            'description': (
                'Deleted accounts are kept in full. They cannot log in and are hidden '
                'from the app\'s user listings, but stay visible here. Use the Restore '
                'action to bring one back.'
            ),
        }),
    )

    def get_queryset(self, request):
        # Deliberately unfiltered: the Django admin is the one place a deleted
        # account always remains visible.
        return super().get_queryset(request)

    @admin.action(description='Soft delete selected users')
    def soft_delete_users(self, request, queryset):
        count = 0
        for user in queryset.filter(is_deleted=False):
            user.soft_delete()
            count += 1
        self.message_user(request, f'{count} user(s) deleted.')

    @admin.action(description='Restore selected users')
    def restore_users(self, request, queryset):
        count = 0
        for user in queryset.filter(is_deleted=True):
            user.restore()
            count += 1
        self.message_user(request, f'{count} user(s) restored.')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    
    list_display = ['user', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
