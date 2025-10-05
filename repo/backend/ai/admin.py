"""
Admin configuration for AI app.
"""
from django.contrib import admin
from .models import UsageLog, UsageLimit


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    """Admin for usage logs."""
    
    list_display = (
        'model',
        'user',
        'organization',
        'workspace',
        'total_tokens',
        'estimated_cost',
        'success',
        'timestamp'
    )
    list_filter = ('model', 'success', 'timestamp', 'organization')
    search_fields = ('user__phone_number', 'organization__name', 'workspace__name')
    readonly_fields = (
        'content',
        'user',
        'workspace',
        'organization',
        'model',
        'prompt_tokens',
        'completion_tokens',
        'total_tokens',
        'estimated_cost',
        'request_duration',
        'success',
        'error_message',
        'timestamp'
    )
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UsageLimit)
class UsageLimitAdmin(admin.ModelAdmin):
    """Admin for usage limits."""
    
    list_display = (
        'scope',
        'scope_id',
        'requests_limit',
        'tokens_limit',
        'cost_limit',
        'period',
        'updated_at'
    )
    list_filter = ('scope', 'period')
    search_fields = ('scope_id',)
    ordering = ('scope', 'scope_id')
