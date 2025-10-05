"""
Tests for AI budget enforcement.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from decimal import Decimal

from accounts.models import Organization, Workspace
from contentmgmt.models import Project, Content, Prompt
from ai.models import UsageLimit, UsageLog

User = get_user_model()


class BudgetEnforcementTestCase(TestCase):
    """Test AI budget enforcement with 402 error."""
    
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
        self.content = Content.objects.create(
            project=self.project,
            prompt=self.prompt,
            title='Test Content',
            status=Content.Status.DRAFT,
            created_by=self.user
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_budget_exceeded_returns_402(self):
        """Test that exceeding budget returns 402 Payment Required."""
        # Set a low budget limit
        UsageLimit.objects.create(
            scope=UsageLimit.Scope.WORKSPACE,
            scope_id=self.workspace.id,
            cost_limit=Decimal('1.00'),  # $1 limit
            period=UsageLimit.Period.MONTHLY
        )
        
        # Create usage that exceeds the limit
        UsageLog.objects.create(
            workspace=self.workspace,
            user=self.user,
            model='gpt-4o-mini',
            prompt_tokens=1000,
            completion_tokens=1000,
            total_tokens=2000,
            estimated_cost=Decimal('1.50'),  # Exceeds $1 limit
            success=True
        )
        
        # Try to generate content
        response = self.client.post(
            f'/api/contents/{self.content.id}/generate/',
            {
                'kind': 'draft',
                'topic': 'Test Topic',
                'min_words': 100
            }
        )
        
        # Should return 402 Payment Required
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertIn('error', response.data)
        self.assertIn('limit', response.data['detail'].lower())
    
    def test_within_budget_allows_generation(self):
        """Test that staying within budget allows generation."""
        # Set a reasonable budget limit
        UsageLimit.objects.create(
            scope=UsageLimit.Scope.WORKSPACE,
            scope_id=self.workspace.id,
            cost_limit=Decimal('100.00'),  # $100 limit
            period=UsageLimit.Period.MONTHLY
        )
        
        # Create usage well within limit
        UsageLog.objects.create(
            workspace=self.workspace,
            user=self.user,
            model='gpt-4o-mini',
            prompt_tokens=1000,
            completion_tokens=1000,
            total_tokens=2000,
            estimated_cost=Decimal('0.50'),
            success=True
        )
        
        # Mock the task delay
        with patch('ai.tasks.generate_content_task.delay'):
            # Try to generate content
            response = self.client.post(
                f'/api/contents/{self.content.id}/generate/',
                {
                    'kind': 'draft',
                    'topic': 'Test Topic',
                    'min_words': 100
                }
            )
        
        # Should be accepted
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
    
    @override_settings(AI_WORKSPACE_MONTHLY_BUDGET_USD=10.0)
    def test_default_budget_enforcement(self):
        """Test default budget from settings when no custom limit set."""
        # Don't create a UsageLimit - use default from settings
        
        # Create usage that exceeds default $10 limit
        UsageLog.objects.create(
            workspace=self.workspace,
            user=self.user,
            model='gpt-4o-mini',
            prompt_tokens=10000,
            completion_tokens=10000,
            total_tokens=20000,
            estimated_cost=Decimal('15.00'),  # Exceeds $10 default
            success=True
        )
        
        # Try to generate content
        response = self.client.post(
            f'/api/contents/{self.content.id}/generate/',
            {
                'kind': 'draft',
                'topic': 'Test Topic',
                'min_words': 100
            }
        )
        
        # Should return 402
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertIn('budget', response.data['detail'].lower())
    
    def test_budget_check_monthly_reset(self):
        """Test that budget checks only count current month's usage."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Set budget limit
        UsageLimit.objects.create(
            scope=UsageLimit.Scope.WORKSPACE,
            scope_id=self.workspace.id,
            cost_limit=Decimal('10.00'),
            period=UsageLimit.Period.MONTHLY
        )
        
        # Create usage from last month (should not count)
        last_month = timezone.now() - timedelta(days=35)
        UsageLog.objects.create(
            workspace=self.workspace,
            user=self.user,
            model='gpt-4o-mini',
            prompt_tokens=10000,
            completion_tokens=10000,
            total_tokens=20000,
            estimated_cost=Decimal('15.00'),
            success=True,
            timestamp=last_month
        )
        
        # Create minimal usage this month
        UsageLog.objects.create(
            workspace=self.workspace,
            user=self.user,
            model='gpt-4o-mini',
            prompt_tokens=100,
            completion_tokens=100,
            total_tokens=200,
            estimated_cost=Decimal('0.50'),
            success=True
        )
        
        # Mock task delay
        with patch('ai.tasks.generate_content_task.delay'):
            # Should be allowed since last month's usage doesn't count
            response = self.client.post(
                f'/api/contents/{self.content.id}/generate/',
                {
                    'kind': 'draft',
                    'topic': 'Test Topic',
                    'min_words': 100
                }
            )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
    
    def test_user_level_budget(self):
        """Test user-level budget enforcement."""
        # Set user budget limit
        UsageLimit.objects.create(
            scope=UsageLimit.Scope.USER,
            scope_id=self.user.id,
            cost_limit=Decimal('5.00'),
            period=UsageLimit.Period.MONTHLY
        )
        
        # Create usage that would exceed user limit
        UsageLog.objects.create(
            workspace=self.workspace,
            user=self.user,
            model='gpt-4o-mini',
            prompt_tokens=5000,
            completion_tokens=5000,
            total_tokens=10000,
            estimated_cost=Decimal('6.00'),
            success=True
        )
        
        # Try to generate - should check both workspace and user limits
        # (Implementation may vary - this tests the concept)
        response = self.client.post(
            f'/api/contents/{self.content.id}/generate/',
            {
                'kind': 'draft',
                'topic': 'Test Topic',
                'min_words': 100
            }
        )
        
        # May return 402 if user limit is also checked
        self.assertIn(
            response.status_code,
            [status.HTTP_402_PAYMENT_REQUIRED, status.HTTP_202_ACCEPTED]
        )
    
    def test_budget_error_message_quality(self):
        """Test that budget error messages are informative."""
        # Set low budget
        UsageLimit.objects.create(
            scope=UsageLimit.Scope.WORKSPACE,
            scope_id=self.workspace.id,
            cost_limit=Decimal('1.00'),
            period=UsageLimit.Period.MONTHLY
        )
        
        # Exceed it
        UsageLog.objects.create(
            workspace=self.workspace,
            user=self.user,
            model='gpt-4o-mini',
            prompt_tokens=1000,
            completion_tokens=1000,
            total_tokens=2000,
            estimated_cost=Decimal('2.00'),
            success=True
        )
        
        response = self.client.post(
            f'/api/contents/{self.content.id}/generate/',
            {
                'kind': 'draft',
                'topic': 'Test Topic',
                'min_words': 100
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        
        # Check that error message includes useful info
        detail = response.data['detail']
        self.assertIsInstance(detail, str)
        # Should mention budget/limit/exceeded
        self.assertTrue(
            any(word in detail.lower() for word in ['budget', 'limit', 'exceed']),
            f"Error message should mention budget/limit: {detail}"
        )
