"""
Models for AI usage tracking and limits.
"""
from django.db import models
from django.conf import settings
from accounts.models import Organization, Workspace
from contentmgmt.models import Content


class UsageLog(models.Model):
    """Log of OpenAI API usage for tracking and billing."""
    
    content = models.ForeignKey(
        Content,
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
