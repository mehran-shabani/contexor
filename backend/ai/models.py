"""
Models for AI usage tracking, limits, and jobs.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import Organization, Workspace


class AiJob(models.Model):
    """Track AI content generation jobs."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    content = models.ForeignKey(
        'contentmgmt.Content',
        on_delete=models.CASCADE,
        related_name='ai_jobs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ai_jobs'
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='ai_jobs'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    kind = models.CharField(max_length=20)  # outline, draft, rewrite, caption
    params = models.JSONField(default=dict)
    result_data = models.JSONField(default=dict, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_jobs'
        indexes = [
            models.Index(fields=['content']),
            models.Index(fields=['user']),
            models.Index(fields=['workspace']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AiJob {self.id} - {self.kind} - {self.status}"
    
    def mark_running(self):
        """Mark job as running."""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])
    
    def mark_completed(self, result_data=None):
        """Mark job as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        if result_data:
            self.result_data = result_data
        self.save(update_fields=['status', 'completed_at', 'result_data', 'updated_at'])
    
    def mark_failed(self, error_message):
        """Mark job as failed."""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'completed_at', 'retry_count', 'updated_at'])


class UsageLog(models.Model):
    """Log of OpenAI API usage for tracking and billing."""
    
    content = models.ForeignKey(
        'contentmgmt.Content',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usage_logs'
    )
    ai_job = models.ForeignKey(
        AiJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usage_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='usage_logs'
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.SET_NULL,
        null=True,
        related_name='usage_logs'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        related_name='usage_logs'
    )
    model = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    total_tokens = models.IntegerField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6)
    request_duration = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usage_logs'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['workspace', '-timestamp']),
            models.Index(fields=['organization', '-timestamp']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['model']),
        ]
    
    def __str__(self):
        return f"{self.model} - {self.total_tokens} tokens - {self.timestamp}"


class UsageLimit(models.Model):
    """Usage limits for users, workspaces, or organizations."""
    
    class Scope(models.TextChoices):
        USER = 'user', 'User'
        WORKSPACE = 'workspace', 'Workspace'
        ORGANIZATION = 'organization', 'Organization'
    
    class Period(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        DAILY = 'daily', 'Daily'
    
    scope = models.CharField(max_length=20, choices=Scope.choices)
    scope_id = models.IntegerField()
    requests_limit = models.IntegerField(null=True, blank=True)
    tokens_limit = models.IntegerField(null=True, blank=True)
    cost_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    period = models.CharField(
        max_length=20,
        choices=Period.choices,
        default=Period.MONTHLY
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'usage_limits'
        unique_together = [['scope', 'scope_id']]
        indexes = [
            models.Index(fields=['scope', 'scope_id']),
        ]
    
    def __str__(self):
        return f"{self.scope} {self.scope_id} - {self.period} limit"


class AuditLog(models.Model):
    """Audit log for content approval and status changes."""
    
    class Action(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        DELETED = 'deleted', 'Deleted'
        STATUS_CHANGED = 'status_changed', 'Status Changed'
    
    content = models.ForeignKey(
        'contentmgmt.Content',
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    old_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20, blank=True, null=True)
    changes = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['content']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['-timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} by {self.user} on {self.content} at {self.timestamp}"


class AiUsage(models.Model):
    """
    Aggregated AI usage statistics.
    This is an alias/view model for UsageLog to match naming in requirements.
    """
    
    class Meta:
        proxy = True
        verbose_name = 'AI Usage'
        verbose_name_plural = 'AI Usage'
