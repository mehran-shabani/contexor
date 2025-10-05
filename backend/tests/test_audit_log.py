"""
Tests for audit logging.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import Organization, Workspace
from contentmgmt.models import Project, Content, Prompt
from ai.models import AuditLog

User = get_user_model()


class AuditLogTestCase(TestCase):
    """Test audit log creation for content actions."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create user and workspace
        self.user = User.objects.create_user(
            phone_number='+989123456789',
            is_active=True
        )
        self.org = Organization.objects.create(
            name='Test Org',
            slug='test-org'
        )
        self.workspace = Workspace.objects.create(
            organization=self.org,
            name='Test Workspace',
            slug='test-workspace'
        )
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user
        )
        self.prompt = Prompt.objects.create(
            workspace=self.workspace,
            title='Test Prompt',
            prompt_template='Test template',
            created_by=self.user
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_audit_log_on_content_create(self):
        """Test that audit log is created when content is created."""
        initial_count = AuditLog.objects.count()
        
        response = self.client.post('/api/contents/', {
            'title': 'New Content',
            'project': self.project.id,
            'prompt': self.prompt.id,
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check audit log was created
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        audit_log = AuditLog.objects.latest('timestamp')
        self.assertEqual(audit_log.action, AuditLog.Action.CREATED)
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.content.title, 'New Content')
        self.assertIsNotNone(audit_log.new_status)
    
    def test_audit_log_on_content_approve(self):
        """Test that audit log is created when content is approved."""
        # Create content in review status
        content = Content.objects.create(
            project=self.project,
            prompt=self.prompt,
            title='Content to Approve',
            body='Test body',
            status=Content.Status.REVIEW,
            created_by=self.user
        )
        
        initial_count = AuditLog.objects.count()
        
        # Approve the content
        response = self.client.post(f'/api/contents/{content.id}/approve/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check audit log was created for approval
        approval_logs = AuditLog.objects.filter(
            content=content,
            action=AuditLog.Action.APPROVED
        )
        self.assertTrue(approval_logs.exists())
        
        audit_log = approval_logs.latest('timestamp')
        self.assertEqual(audit_log.action, AuditLog.Action.APPROVED)
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.old_status, Content.Status.REVIEW)
        self.assertEqual(audit_log.new_status, Content.Status.APPROVED)
    
    def test_audit_log_on_content_reject(self):
        """Test that audit log is created when content is rejected."""
        # Create content in review status
        content = Content.objects.create(
            project=self.project,
            prompt=self.prompt,
            title='Content to Reject',
            body='Test body',
            status=Content.Status.REVIEW,
            created_by=self.user
        )
        
        # Reject the content
        response = self.client.post(
            f'/api/contents/{content.id}/reject/',
            {'reason': 'Quality issues'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check audit log was created for rejection
        rejection_logs = AuditLog.objects.filter(
            content=content,
            action=AuditLog.Action.REJECTED
        )
        self.assertTrue(rejection_logs.exists())
        
        audit_log = rejection_logs.latest('timestamp')
        self.assertEqual(audit_log.action, AuditLog.Action.REJECTED)
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.old_status, Content.Status.REVIEW)
        self.assertEqual(audit_log.new_status, Content.Status.REJECTED)
        self.assertIn('Quality issues', audit_log.notes)
    
    def test_audit_log_includes_metadata(self):
        """Test that audit log includes IP address and user agent."""
        response = self.client.post(
            '/api/contents/',
            {
                'title': 'Test Content',
                'project': self.project.id,
                'prompt': self.prompt.id,
            },
            HTTP_USER_AGENT='TestClient/1.0'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        audit_log = AuditLog.objects.latest('timestamp')
        self.assertIsNotNone(audit_log.ip_address)
        self.assertIn('TestClient', audit_log.user_agent)
    
    def test_audit_log_status_change_on_generate(self):
        """Test that audit log records status change when generation starts."""
        from unittest.mock import patch
        
        content = Content.objects.create(
            project=self.project,
            prompt=self.prompt,
            title='Content to Generate',
            status=Content.Status.DRAFT,
            created_by=self.user
        )
        
        initial_count = AuditLog.objects.filter(content=content).count()
        
        # Mock usage limit check and task delay
        with patch('ai.services.check_workspace_usage_limits', return_value=(True, 'OK')):
            with patch('ai.tasks.generate_content_task.delay'):
                response = self.client.post(
                    f'/api/contents/{content.id}/generate/',
                    {
                        'kind': 'draft',
                        'topic': 'Test Topic',
                        'min_words': 100
                    }
                )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        
        # Check audit log was created for status change
        status_change_logs = AuditLog.objects.filter(
            content=content,
            action=AuditLog.Action.STATUS_CHANGED
        )
        self.assertTrue(status_change_logs.exists())
        
        audit_log = status_change_logs.latest('timestamp')
        self.assertEqual(audit_log.old_status, Content.Status.DRAFT)
        self.assertEqual(audit_log.new_status, Content.Status.IN_PROGRESS)
        self.assertIn('AI generation job created', audit_log.notes)
    
    def test_audit_log_ordering(self):
        """Test that audit logs are ordered by timestamp descending."""
        content = Content.objects.create(
            project=self.project,
            prompt=self.prompt,
            title='Test Content',
            status=Content.Status.DRAFT,
            created_by=self.user
        )
        
        # Get all logs for this content
        logs = AuditLog.objects.filter(content=content).order_by('-timestamp')
        
        # Verify ordering
        timestamps = [log.timestamp for log in logs]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))


class AuditLogQueryTestCase(TestCase):
    """Test audit log querying and filtering."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            phone_number='+989123456789',
            is_active=True
        )
        self.org = Organization.objects.create(
            name='Test Org',
            slug='test-org'
        )
        self.workspace = Workspace.objects.create(
            organization=self.org,
            name='Test Workspace',
            slug='test-workspace'
        )
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user
        )
        self.prompt = Prompt.objects.create(
            workspace=self.workspace,
            title='Test Prompt',
            prompt_template='Test template',
            created_by=self.user
        )
        self.content = Content.objects.create(
            project=self.project,
            prompt=self.prompt,
            title='Test Content',
            created_by=self.user
        )
    
    def test_filter_by_action(self):
        """Test filtering audit logs by action type."""
        # Create various audit log entries
        AuditLog.objects.create(
            content=self.content,
            user=self.user,
            action=AuditLog.Action.CREATED
        )
        AuditLog.objects.create(
            content=self.content,
            user=self.user,
            action=AuditLog.Action.UPDATED
        )
        
        # Filter by action
        created_logs = AuditLog.objects.filter(action=AuditLog.Action.CREATED)
        self.assertTrue(created_logs.exists())
        
        approved_logs = AuditLog.objects.filter(action=AuditLog.Action.APPROVED)
        self.assertFalse(approved_logs.exists())
    
    def test_filter_by_user(self):
        """Test filtering audit logs by user."""
        user2 = User.objects.create_user(
            phone_number='+989987654321',
            is_active=True
        )
        
        AuditLog.objects.create(
            content=self.content,
            user=self.user,
            action=AuditLog.Action.CREATED
        )
        AuditLog.objects.create(
            content=self.content,
            user=user2,
            action=AuditLog.Action.UPDATED
        )
        
        # Filter by user
        user1_logs = AuditLog.objects.filter(user=self.user)
        self.assertEqual(user1_logs.count(), 1)
        
        user2_logs = AuditLog.objects.filter(user=user2)
        self.assertEqual(user2_logs.count(), 1)
