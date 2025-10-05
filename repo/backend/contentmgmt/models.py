"""
Models for content management.
"""
from django.db import models
from django.conf import settings
from accounts.models import Workspace


class Project(models.Model):
    """Project model for organizing content."""
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'projects'
        unique_together = [['workspace', 'slug']]
        indexes = [
            models.Index(fields=['workspace']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.workspace.name} - {self.name}"


class Prompt(models.Model):
    """Reusable prompts for content generation."""
    
    class Category(models.TextChoices):
        BLOG = 'blog', 'Blog Post'
        SOCIAL = 'social', 'Social Media'
        ECOMMERCE = 'ecommerce', 'E-commerce'
        EMAIL = 'email', 'Email Marketing'
        AD = 'ad', 'Advertisement'
        OTHER = 'other', 'Other'
    
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=Category.choices)
    prompt_template = models.TextField()
    variables = models.JSONField(default=list)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prompts'
    )
    is_public = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_prompts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prompts'
        indexes = [
            models.Index(fields=['workspace']),
            models.Index(fields=['category']),
            models.Index(fields=['is_public']),
            models.Index(fields=['-usage_count']),
        ]
    
    def __str__(self):
        return self.title


class Content(models.Model):
    """AI-generated content with workflow status."""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        IN_PROGRESS = 'in_progress', 'In Progress'
        REVIEW = 'review', 'Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='contents'
    )
    prompt = models.ForeignKey(
        Prompt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contents'
    )
    prompt_variables = models.JSONField(default=dict)
    word_count = models.IntegerField(default=0)
    has_pii = models.BooleanField(default=False)
    pii_warnings = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    current_version = models.ForeignKey(
        'ContentVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_for_content',
        help_text='Current active version of this content'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contents'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_contents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'contents'
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['prompt']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['has_pii']),
        ]
    
    def __str__(self):
        return self.title


class ContentVersion(models.Model):
    """
    Content version snapshots with Markdown RTL support.
    Each version stores the full content at a point in time.
    """
    
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    title = models.CharField(max_length=500)
    body_markdown = models.TextField(
        help_text='Content body in Markdown format with RTL support'
    )
    metadata = models.JSONField(
        default=dict,
        help_text='Additional metadata like meta description, keywords, etc.'
    )
    word_count = models.IntegerField(default=0)
    ai_job = models.ForeignKey(
        'ai.AiJob',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='content_versions',
        help_text='AI job that created this version'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_content_versions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'content_versions'
        unique_together = [['content', 'version_number']]
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['content', '-version_number']),
            models.Index(fields=['ai_job']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.content.title} - v{self.version_number}"
    
    def save(self, *args, **kwargs):
        """Calculate word count on save."""
        if self.body_markdown:
            # Simple word count (split by whitespace)
            self.word_count = len(self.body_markdown.split())
        super().save(*args, **kwargs)


# Keep old Version model for backward compatibility
class Version(models.Model):
    """
    Legacy version model - kept for backward compatibility.
    New code should use ContentVersion instead.
    """
    
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='legacy_versions'
    )
    version_number = models.IntegerField()
    content_snapshot = models.JSONField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_legacy_versions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'versions'
        unique_together = [['content', 'version_number']]
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['content', '-version_number']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.content.title} - v{self.version_number}"
