"""
Views for content management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Project, Prompt, Content, Version
from .serializers import (
    ProjectSerializer, PromptSerializer,
    ContentSerializer, ContentListSerializer, VersionSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project CRUD."""
    
    queryset = Project.objects.select_related('workspace', 'created_by')
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['workspace', 'is_active']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PromptViewSet(viewsets.ModelViewSet):
    """ViewSet for Prompt CRUD."""
    
    queryset = Prompt.objects.select_related('workspace', 'created_by')
    serializer_class = PromptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['workspace', 'category', 'is_public']
    search_fields = ['title', 'prompt_template']
    ordering_fields = ['title', 'usage_count', 'created_at']
    ordering = ['-usage_count', '-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContentViewSet(viewsets.ModelViewSet):
    """ViewSet for Content CRUD."""
    
    queryset = Content.objects.select_related(
        'project', 'prompt', 'created_by', 'approved_by'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'status', 'has_pii']
    search_fields = ['title', 'body']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContentListSerializer
        return ContentSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve content and create version."""
        content = self.get_object()
        
        if content.status != Content.Status.REVIEW:
            return Response(
                {'error': 'Content must be in review status to approve'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update content status
        content.status = Content.Status.APPROVED
        content.approved_by = request.user
        from django.utils import timezone
        content.approved_at = timezone.now()
        content.save()
        
        # Create version snapshot
        version_number = content.versions.count() + 1
        Version.objects.create(
            content=content,
            version_number=version_number,
            content_snapshot={
                'title': content.title,
                'body': content.body,
                'metadata': content.metadata,
                'word_count': content.word_count,
            },
            created_by=request.user
        )
        
        serializer = self.get_serializer(content)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject content."""
        content = self.get_object()
        
        if content.status != Content.Status.REVIEW:
            return Response(
                {'error': 'Content must be in review status to reject'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('reason', '')
        content.status = Content.Status.REJECTED
        content.rejection_reason = rejection_reason
        content.save()
        
        serializer = self.get_serializer(content)
        return Response(serializer.data)


class VersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Version (read-only)."""
    
    queryset = Version.objects.select_related('content', 'created_by')
    serializer_class = VersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['content']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']
