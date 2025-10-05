"""
Views for AI operations and usage tracking.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import timedelta
import logging

from .models import AiJob, UsageLog, UsageLimit, AuditLog
from .serializers import (
    AiJobSerializer, UsageLogSerializer, UsageLimitSerializer,
    AuditLogSerializer, UsageSummarySerializer
)
from .services import get_usage_summary

logger = logging.getLogger(__name__)


class AiJobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AiJob (read-only)."""
    
    queryset = AiJob.objects.select_related('content', 'user', 'workspace')
    serializer_class = AiJobSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['content', 'user', 'workspace', 'status', 'kind']
    ordering_fields = ['created_at', 'started_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by user's accessible workspaces."""
        user = self.request.user
        # For now, return all. In production, filter by user's workspaces
        return self.queryset


class UsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for UsageLog (read-only)."""
    
    queryset = UsageLog.objects.select_related('content', 'ai_job', 'user', 'workspace', 'organization')
    serializer_class = UsageLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['workspace', 'organization', 'user', 'model', 'success']
    ordering_fields = ['timestamp', 'total_tokens', 'estimated_cost']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter by user's accessible workspaces."""
        user = self.request.user
        # For now, return all. In production, filter by user's workspaces
        return self.queryset


class UsageLimitViewSet(viewsets.ModelViewSet):
    """ViewSet for UsageLimit CRUD."""
    
    queryset = UsageLimit.objects.all()
    serializer_class = UsageLimitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['scope', 'scope_id', 'period']


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AuditLog (read-only)."""
    
    queryset = AuditLog.objects.select_related('content', 'user')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['content', 'user', 'action']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']


@api_view(['GET'])
def usage_summary(request):
    """
    Get usage summary.
    
    GET /api/usage/summary/?workspace_id=1&period=monthly
    
    Query params:
        - workspace_id: Filter by workspace
        - user_id: Filter by user
        - organization_id: Filter by organization
        - period: 'monthly' (default), 'weekly', 'daily', 'all'
    """
    workspace_id = request.query_params.get('workspace_id')
    user_id = request.query_params.get('user_id')
    organization_id = request.query_params.get('organization_id')
    period = request.query_params.get('period', 'monthly')
    
    # Calculate date range based on period
    now = timezone.now()
    
    if period == 'monthly':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'weekly':
        start_date = now - timedelta(days=7)
    elif period == 'daily':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:  # all
        start_date = None
    
    end_date = now
    
    # Get instances if IDs provided
    workspace = None
    user = None
    organization = None
    
    if workspace_id:
        from accounts.models import Workspace
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response(
                {'error': 'Workspace not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    if user_id:
        from accounts.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    if organization_id:
        from accounts.models import Organization
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Get summary
    summary = get_usage_summary(
        workspace=workspace,
        user=user,
        organization=organization,
        start_date=start_date,
        end_date=end_date
    )
    
    serializer = UsageSummarySerializer(summary)
    
    return Response({
        'period': period,
        'start_date': start_date.isoformat() if start_date else None,
        'end_date': end_date.isoformat(),
        'summary': serializer.data
    })
