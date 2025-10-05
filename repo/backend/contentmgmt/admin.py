"""
Admin configuration for content management.
"""
from django.contrib import admin
from .models import Project, Prompt, Content, ContentVersion, Version


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for Project model."""
    
    list_display = ['id', 'name', 'slug', 'workspace', 'is_active', 'created_at']
    list_filter = ['is_active', 'workspace', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    """Admin for Prompt model."""
    
    list_display = ['id', 'title', 'category', 'is_public', 'usage_count', 'workspace']
    list_filter = ['category', 'is_public', 'workspace']
    search_fields = ['title', 'prompt_template']
    readonly_fields = ['usage_count']


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    """Admin for Content model."""
    
    list_display = ['id', 'title', 'status', 'project', 'has_pii', 'word_count', 'created_at']
    list_filter = ['status', 'has_pii', 'project', 'created_at']
    search_fields = ['title', 'body']
    readonly_fields = ['word_count', 'created_at', 'updated_at', 'approved_at']


@admin.register(ContentVersion)
class ContentVersionAdmin(admin.ModelAdmin):
    """Admin for ContentVersion model."""
    
    list_display = ['id', 'content', 'version_number', 'word_count', 'ai_job', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content__title', 'title']
    readonly_fields = ['version_number', 'word_count', 'created_at']


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    """Admin for legacy Version model."""
    
    list_display = ['id', 'content', 'version_number', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content__title']
    readonly_fields = ['created_at']
