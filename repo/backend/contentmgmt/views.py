"""
Views for content management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
import logging

from .models import Project, Prompt, Content, Version, ContentVersion
from .serializers import (
    ProjectSerializer, PromptSerializer,
    ContentSerializer, ContentListSerializer, 
    VersionSerializer, ContentVersionSerializer,
    GenerateContentSerializer
)
from ai.models import AiJob, AuditLog

logger = logging.getLogger(__name__)


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
        content = serializer.save(created_by=self.request.user)
        
        # Create audit log
        AuditLog.objects.create(
            content=content,
            user=self.request.user,
            action=AuditLog.Action.CREATED,
            new_status=content.status,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """
        Queue AI content generation job.
        
        POST /api/contents/:id/generate/
        {
            "kind": "draft",
            "topic": "مزایای هوش مصنوعی",
            "tone": "حرفه‌ای",
            "audience": "کارآفرینان",
            "keywords": "هوش مصنوعی، نوآوری، کسب‌وکار",
            "min_words": 800
        }
        """
        content = self.get_object()
        serializer = GenerateContentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        params = serializer.validated_data
        
        # Get workspace from content's project
        workspace = content.project.workspace
        
        # Check usage limits before creating job
        from ai.services import check_workspace_usage_limits
        limits_ok, limits_message = check_workspace_usage_limits(workspace)
        
        if not limits_ok:
            return Response(
                {
                    'error': 'Usage limit exceeded',
                    'detail': limits_message
                },
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        # Create AI job
        job = AiJob.objects.create(
            content=content,
            user=request.user,
            workspace=workspace,
            kind=params['kind'],
            params=params,
            status=AiJob.Status.PENDING
        )
        
        # Update content status to in_progress
        old_status = content.status
        content.status = Content.Status.IN_PROGRESS
        content.save(update_fields=['status', 'updated_at'])
        
        # Create audit log
        AuditLog.objects.create(
            content=content,
            user=request.user,
            action=AuditLog.Action.STATUS_CHANGED,
            old_status=old_status,
            new_status=content.status,
            changes={'job_id': job.id},
            notes=f"AI generation job created: {params['kind']}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        # Queue the task
        from ai.tasks import generate_content_task
        generate_content_task.delay(content.id, params, job.id)
        
        logger.info(f"Content generation job {job.id} queued for content {content.id}")
        
        return Response({
            'job_id': job.id,
            'status': job.status,
            'message': 'Content generation started',
            'content': ContentSerializer(content).data
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        Get all versions for a content.
        
        GET /api/contents/:id/versions/
        """
        content = self.get_object()
        versions = content.versions.all()
        serializer = ContentVersionSerializer(versions, many=True)
        return Response(serializer.data)
    
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
        old_status = content.status
        content.status = Content.Status.APPROVED
        content.approved_by = request.user
        content.approved_at = timezone.now()
        content.save()
        
        # Create audit log
        AuditLog.objects.create(
            content=content,
            user=request.user,
            action=AuditLog.Action.APPROVED,
            old_status=old_status,
            new_status=content.status,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        logger.info(f"Content {content.id} approved by user {request.user.id}")
        
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
        old_status = content.status
        content.status = Content.Status.REJECTED
        content.rejection_reason = rejection_reason
        content.save()
        
        # Create audit log
        AuditLog.objects.create(
            content=content,
            user=request.user,
            action=AuditLog.Action.REJECTED,
            old_status=old_status,
            new_status=content.status,
            notes=rejection_reason,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        logger.info(f"Content {content.id} rejected by user {request.user.id}")
        
        serializer = self.get_serializer(content)
        return Response(serializer.data)


class ContentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ContentVersion (read-only)."""
    
    queryset = ContentVersion.objects.select_related('content', 'created_by', 'ai_job')
    serializer_class = ContentVersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['content', 'ai_job']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']


class VersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for legacy Version (read-only)."""
    
    queryset = Version.objects.select_related('content', 'created_by')
    serializer_class = VersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['content']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']
