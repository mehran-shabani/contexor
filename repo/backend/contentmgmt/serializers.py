"""
Serializers for content management.
"""
from rest_framework import serializers
from .models import Project, Prompt, Content, Version, ContentVersion


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""
    
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    content_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'slug', 'workspace', 'workspace_name',
            'description', 'created_by', 'created_by_name',
            'is_active', 'created_at', 'updated_at', 'content_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_content_count(self, obj):
        return obj.contents.count()


class PromptSerializer(serializers.ModelSerializer):
    """Serializer for Prompt model."""
    
    workspace_name = serializers.CharField(source='workspace.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Prompt
        fields = [
            'id', 'title', 'category', 'prompt_template', 'variables',
            'workspace', 'workspace_name', 'is_public', 'usage_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'usage_count', 'created_at', 'updated_at']


class ContentSerializer(serializers.ModelSerializer):
    """Serializer for Content model."""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    prompt_title = serializers.CharField(source='prompt.title', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'body', 'status', 'project', 'project_name',
            'prompt', 'prompt_title', 'prompt_variables', 'word_count',
            'has_pii', 'pii_warnings', 'metadata',
            'created_by', 'created_by_name', 'approved_by', 'approved_by_name',
            'created_at', 'updated_at', 'approved_at', 'rejection_reason'
        ]
        read_only_fields = [
            'id', 'created_by', 'word_count', 'has_pii', 'pii_warnings',
            'metadata', 'created_at', 'updated_at', 'approved_at'
        ]


class ContentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for content list."""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'status', 'project', 'project_name',
            'word_count', 'has_pii', 'created_at', 'updated_at'
        ]


class ContentVersionSerializer(serializers.ModelSerializer):
    """Serializer for ContentVersion model."""
    
    content_title = serializers.CharField(source='content.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = ContentVersion
        fields = [
            'id', 'content', 'content_title', 'version_number',
            'title', 'body_markdown', 'metadata', 'word_count',
            'ai_job', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'version_number', 'word_count', 'created_by', 'created_at']


class VersionSerializer(serializers.ModelSerializer):
    """Serializer for legacy Version model."""
    
    content_title = serializers.CharField(source='content.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Version
        fields = [
            'id', 'content', 'content_title', 'version_number',
            'content_snapshot', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class GenerateContentSerializer(serializers.Serializer):
    """Serializer for content generation request."""
    
    kind = serializers.ChoiceField(
        choices=['outline', 'draft', 'rewrite', 'caption'],
        required=True,
        help_text='Type of content to generate'
    )
    topic = serializers.CharField(
        max_length=500,
        required=False,
        help_text='Content topic'
    )
    tone = serializers.CharField(
        max_length=100,
        required=False,
        default='professional',
        help_text='Tone of the content (e.g., professional, casual, friendly)'
    )
    audience = serializers.CharField(
        max_length=200,
        required=False,
        default='general',
        help_text='Target audience'
    )
    keywords = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='Comma-separated keywords'
    )
    min_words = serializers.IntegerField(
        required=False,
        default=500,
        min_value=100,
        max_value=5000,
        help_text='Minimum word count'
    )
    max_words = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=100,
        max_value=10000,
        help_text='Maximum word count'
    )
    additional_instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Any additional instructions for the AI'
    )
