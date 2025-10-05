"""
Serializers for AI models.
"""
from rest_framework import serializers
from .models import AiJob, UsageLog, UsageLimit, AuditLog


class AiJobSerializer(serializers.ModelSerializer):
    """Serializer for AiJob model."""
    
    content_title = serializers.CharField(source='content.title', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True, allow_null=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    
    class Meta:
        model = AiJob
        fields = [
            'id', 'content', 'content_title', 'user', 'user_name',
            'workspace', 'workspace_name', 'status', 'kind', 'params',
            'result_data', 'error_message', 'retry_count',
            'started_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'result_data', 'error_message', 'retry_count',
            'started_at', 'completed_at', 'created_at', 'updated_at'
        ]


class UsageLogSerializer(serializers.ModelSerializer):
    """Serializer for UsageLog model."""
    
    content_title = serializers.CharField(source='content.title', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = UsageLog
        fields = [
            'id', 'content', 'content_title', 'ai_job', 'user', 'user_name',
            'workspace', 'organization', 'model', 'prompt_tokens',
            'completion_tokens', 'total_tokens', 'estimated_cost',
            'request_duration', 'success', 'error_message', 'timestamp'
        ]
        read_only_fields = '__all__'


class UsageLimitSerializer(serializers.ModelSerializer):
    """Serializer for UsageLimit model."""
    
    class Meta:
        model = UsageLimit
        fields = [
            'id', 'scope', 'scope_id', 'requests_limit',
            'tokens_limit', 'cost_limit', 'period',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""
    
    content_title = serializers.CharField(source='content.title', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'content', 'content_title', 'user', 'user_name',
            'action', 'old_status', 'new_status', 'changes', 'notes',
            'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = '__all__'


class UsageSummarySerializer(serializers.Serializer):
    """Serializer for usage summary response."""
    
    total_requests = serializers.IntegerField()
    total_prompt_tokens = serializers.IntegerField()
    total_completion_tokens = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    total_cost = serializers.FloatField()
    model_breakdown = serializers.DictField()
