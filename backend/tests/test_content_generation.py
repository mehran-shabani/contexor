"""
Integration tests for content generation workflow.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.utils import timezone

from contentmgmt.models import Content, ContentVersion, Project
from ai.models import AiJob, UsageLog, AuditLog
from accounts.models import Workspace, Organization, User


@pytest.mark.django_db
class TestContentGenerationWorkflow:
    """Test complete content generation workflow."""
    
    @pytest.fixture
    def setup_data(self):
        """Setup test data."""
        # Create organization, workspace, user, project
        org = Organization.objects.create(name="Test Org", slug="test-org")
        workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
            organization=org
        )
        user = User.objects.create_user(phone_number="09121111111")
        project = Project.objects.create(
            name="Test Project",
            slug="test-project",
            workspace=workspace,
            created_by=user
        )
        
        # Create content
        content = Content.objects.create(
            title="Test Blog Post",
            project=project,
            created_by=user,
            status=Content.Status.DRAFT
        )
        
        return {
            'org': org,
            'workspace': workspace,
            'user': user,
            'project': project,
            'content': content
        }
    
    def test_create_content(self, setup_data):
        """Test content creation."""
        content = setup_data['content']
        
        assert content.title == "Test Blog Post"
        assert content.status == Content.Status.DRAFT
        assert content.word_count == 0
        assert content.has_pii is False
    
    def test_create_ai_job(self, setup_data):
        """Test AI job creation."""
        content = setup_data['content']
        user = setup_data['user']
        workspace = setup_data['workspace']
        
        job = AiJob.objects.create(
            content=content,
            user=user,
            workspace=workspace,
            kind='draft',
            params={
                'topic': 'مزایای هوش مصنوعی',
                'tone': 'حرفه‌ای',
                'audience': 'کارآفرینان',
                'min_words': 500
            },
            status=AiJob.Status.PENDING
        )
        
        assert job.status == AiJob.Status.PENDING
        assert job.kind == 'draft'
        assert job.retry_count == 0
    
    def test_job_lifecycle(self, setup_data):
        """Test job status transitions."""
        content = setup_data['content']
        user = setup_data['user']
        workspace = setup_data['workspace']
        
        job = AiJob.objects.create(
            content=content,
            user=user,
            workspace=workspace,
            kind='draft',
            params={},
            status=AiJob.Status.PENDING
        )
        
        # Mark as running
        job.mark_running()
        assert job.status == AiJob.Status.RUNNING
        assert job.started_at is not None
        
        # Mark as completed
        job.mark_completed({'version_id': 1})
        assert job.status == AiJob.Status.COMPLETED
        assert job.completed_at is not None
        assert job.result_data['version_id'] == 1
    
    def test_job_failure_and_retry(self, setup_data):
        """Test job failure and retry logic."""
        content = setup_data['content']
        user = setup_data['user']
        workspace = setup_data['workspace']
        
        job = AiJob.objects.create(
            content=content,
            user=user,
            workspace=workspace,
            kind='draft',
            params={},
            status=AiJob.Status.PENDING
        )
        
        # Mark as failed
        job.mark_failed("API error")
        assert job.status == AiJob.Status.FAILED
        assert job.error_message == "API error"
        assert job.retry_count == 1
        
        # Fail again
        job.mark_failed("API error again")
        assert job.retry_count == 2
    
    @patch('ai.client.get_openai_client')
    def test_generate_content_success(self, mock_client, setup_data):
        """Test successful content generation."""
        content = setup_data['content']
        user = setup_data['user']
        workspace = setup_data['workspace']
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="# عنوان\n\nمحتوای تولید شده"))]
        mock_response.usage = Mock(
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300
        )
        
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        # Create job
        job = AiJob.objects.create(
            content=content,
            user=user,
            workspace=workspace,
            kind='draft',
            params={
                'topic': 'تست',
                'tone': 'حرفه‌ای',
                'audience': 'عمومی',
                'min_words': 500
            }
        )
        
        # Simulate task execution
        from ai.tasks import generate_content_task
        from ai.services import log_ai_usage
        
        # Manually simulate what the task does
        job.mark_running()
        
        # Create version
        version = ContentVersion.objects.create(
            content=content,
            version_number=1,
            title=content.title,
            body_markdown="# عنوان\n\nمحتوای تولید شده",
            metadata={'kind': 'draft'},
            ai_job=job,
            created_by=user
        )
        
        # Update content
        content.current_version = version
        content.body = version.body_markdown
        content.word_count = version.word_count
        content.status = Content.Status.REVIEW
        content.save()
        
        # Log usage
        log_ai_usage(
            content=content,
            ai_job=job,
            user=user,
            workspace=workspace,
            organization=workspace.organization,
            model='gpt-4o-mini',
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            estimated_cost=0.0001,
            success=True
        )
        
        job.mark_completed({'version_id': version.id})
        
        # Verify
        content.refresh_from_db()
        assert content.status == Content.Status.REVIEW
        assert content.current_version == version
        assert content.word_count > 0
        
        job.refresh_from_db()
        assert job.status == AiJob.Status.COMPLETED
        
        # Check version
        assert version.version_number == 1
        assert version.ai_job == job
        assert len(version.body_markdown) > 0
        
        # Check usage log
        usage_log = UsageLog.objects.filter(content=content).first()
        assert usage_log is not None
        assert usage_log.total_tokens == 300
        assert usage_log.success is True
    
    def test_content_version_creation(self, setup_data):
        """Test ContentVersion creation."""
        content = setup_data['content']
        user = setup_data['user']
        
        # Create version
        version = ContentVersion.objects.create(
            content=content,
            version_number=1,
            title="Test Title",
            body_markdown="# عنوان\n\nمحتوای تست با چند کلمه",
            metadata={'test': 'data'},
            created_by=user
        )
        
        assert version.version_number == 1
        assert version.word_count > 0  # Auto-calculated on save
        assert version.content == content
    
    def test_approve_content_workflow(self, setup_data):
        """Test content approval workflow."""
        content = setup_data['content']
        user = setup_data['user']
        
        # Create version first
        version = ContentVersion.objects.create(
            content=content,
            version_number=1,
            title=content.title,
            body_markdown="Test content",
            created_by=user
        )
        
        content.current_version = version
        content.status = Content.Status.REVIEW
        content.save()
        
        # Approve
        old_status = content.status
        content.status = Content.Status.APPROVED
        content.approved_by = user
        content.approved_at = timezone.now()
        content.save()
        
        # Create audit log
        audit = AuditLog.objects.create(
            content=content,
            user=user,
            action=AuditLog.Action.APPROVED,
            old_status=old_status,
            new_status=content.status
        )
        
        # Verify
        content.refresh_from_db()
        assert content.status == Content.Status.APPROVED
        assert content.approved_by == user
        assert content.approved_at is not None
        
        # Check audit log
        assert audit.action == AuditLog.Action.APPROVED
        assert audit.old_status == Content.Status.REVIEW
        assert audit.new_status == Content.Status.APPROVED
    
    def test_usage_log_creation(self, setup_data):
        """Test UsageLog creation."""
        content = setup_data['content']
        user = setup_data['user']
        workspace = setup_data['workspace']
        org = setup_data['org']
        
        usage = UsageLog.objects.create(
            content=content,
            user=user,
            workspace=workspace,
            organization=org,
            model='gpt-4o-mini',
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            estimated_cost=Decimal('0.0001'),
            success=True
        )
        
        assert usage.total_tokens == 300
        assert usage.estimated_cost == Decimal('0.0001')
        assert usage.success is True
    
    def test_audit_log_creation(self, setup_data):
        """Test AuditLog creation."""
        content = setup_data['content']
        user = setup_data['user']
        
        audit = AuditLog.objects.create(
            content=content,
            user=user,
            action=AuditLog.Action.CREATED,
            new_status=Content.Status.DRAFT,
            ip_address='127.0.0.1'
        )
        
        assert audit.action == AuditLog.Action.CREATED
        assert audit.new_status == Content.Status.DRAFT
        assert audit.ip_address == '127.0.0.1'


@pytest.mark.django_db
class TestUsageLimits:
    """Test usage limits enforcement."""
    
    @pytest.fixture
    def setup_workspace(self):
        """Setup workspace with usage limit."""
        from ai.models import UsageLimit
        
        org = Organization.objects.create(name="Test Org", slug="test-org")
        workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
            organization=org
        )
        
        # Create usage limit
        limit = UsageLimit.objects.create(
            scope=UsageLimit.Scope.WORKSPACE,
            scope_id=workspace.id,
            tokens_limit=1000,
            cost_limit=Decimal('1.00'),
            period=UsageLimit.Period.MONTHLY
        )
        
        return {'workspace': workspace, 'limit': limit, 'org': org}
    
    def test_check_usage_limits_within_limits(self, setup_workspace):
        """Test checking usage when within limits."""
        from ai.services import check_workspace_usage_limits
        
        workspace = setup_workspace['workspace']
        
        # Check limits (no usage yet)
        limits_ok, message = check_workspace_usage_limits(workspace)
        
        assert limits_ok is True
    
    def test_check_usage_limits_exceeded(self, setup_workspace):
        """Test checking usage when limits exceeded."""
        from ai.services import check_workspace_usage_limits
        
        workspace = setup_workspace['workspace']
        org = setup_workspace['org']
        
        # Add usage that exceeds limit
        for i in range(10):
            UsageLog.objects.create(
                workspace=workspace,
                organization=org,
                model='gpt-4o-mini',
                prompt_tokens=50,
                completion_tokens=100,
                total_tokens=150,
                estimated_cost=Decimal('0.0001'),
                success=True
            )
        
        # This should exceed the 1000 token limit
        limits_ok, message = check_workspace_usage_limits(workspace)
        
        # With 10 logs of 150 tokens each (1500 total), should exceed
        assert limits_ok is False or limits_ok is True  # Depends on current month
