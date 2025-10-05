"""
Admin configuration for content management.
"""
from django.contrib import admin
from .models import Project, Prompt, Content, Version


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for projects."""
    
    list_display = ('name', 'workspace', 'created_by', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'workspace')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    """Admin for prompts."""
    
    list_display = ('title', 'category', 'workspace', 'is_public', 'usage_count', 'created_at')
    list_filter = ('category', 'is_public', 'created_at')
    search_fields = ('title', 'prompt_template')
    ordering = ('-usage_count', '-created_at')


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    """Admin for content."""
    
    list_display = ('title', 'project', 'status', 'has_pii', 'word_count', 'created_by', 'created_at')
    list_filter = ('status', 'has_pii', 'created_at', 'project__workspace')
    search_fields = ('title', 'body')
    ordering = ('-created_at',)
    readonly_fields = ('word_count', 'has_pii', 'pii_warnings', 'metadata')


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    """Admin for versions."""
    
    list_display = ('content', 'version_number', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content__title',)
    ordering = ('-created_at',)
    readonly_fields = ('content_snapshot',)
