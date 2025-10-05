"""
Admin configuration for AI app.
"""
from django.contrib import admin
from .models import AiJob, UsageLog, UsageLimit, AuditLog
from .prompts.models import PromptTemplate


@admin.register(AiJob)
class AiJobAdmin(admin.ModelAdmin):
    """Admin for AiJob model."""
    
    list_display = ['id', 'content', 'kind', 'status', 'user', 'workspace', 'created_at']
    list_filter = ['status', 'kind', 'workspace', 'created_at']
    search_fields = ['content__title', 'user__phone_number', 'workspace__name']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
    date_hierarchy = 'created_at'


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    """Admin for UsageLog model."""
    
    list_display = ['id', 'model', 'total_tokens', 'estimated_cost', 'success', 'workspace', 'timestamp']
    list_filter = ['model', 'success', 'workspace', 'timestamp']
    search_fields = ['content__title', 'user__phone_number', 'workspace__name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(UsageLimit)
class UsageLimitAdmin(admin.ModelAdmin):
    """Admin for UsageLimit model."""
    
    list_display = ['id', 'scope', 'scope_id', 'period', 'requests_limit', 'tokens_limit', 'cost_limit']
    list_filter = ['scope', 'period']
    search_fields = ['scope_id']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin for AuditLog model."""
    
    list_display = ['id', 'content', 'user', 'action', 'old_status', 'new_status', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['content__title', 'user__phone_number']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    """Admin for PromptTemplate model."""
    
    list_display = ['id', 'title', 'kind', 'version', 'is_active', 'usage_count', 'workspace']
    list_filter = ['kind', 'is_active', 'workspace']
    search_fields = ['title', 'template_text']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
