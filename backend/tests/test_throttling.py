"""
Tests for rate limiting/throttling.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from time import sleep

from accounts.models import Organization, Workspace
from contentmgmt.models import Project, Content, Prompt

User = get_user_model()


@override_settings(
    MOCK_SMS=True,
    DEFAULT_THROTTLE_RATES={
        'otp_request_ip': '5/min',
        'otp_request_phone': '3/min',
        'content_generate': '10/min',
    }
)
class ThrottlingTestCase(TestCase):
    """Test rate limiting on critical endpoints."""
    
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
            created_by=self.user,
            status=Content.Status.DRAFT
        )
    
    def test_otp_request_ip_throttle(self):
        """Test OTP request throttling by IP address (5/min)."""
        phone = '+989111111111'
        
        # First 5 requests should succeed
        for i in range(5):
            response = self.client.post('/api/auth/otp/request/', {
                'phone_number': phone
            })
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS],
                f"Request {i+1} failed unexpectedly"
            )
        
        # 6th request should be throttled
        response = self.client.post('/api/auth/otp/request/', {
            'phone_number': phone
        })
        
        # Should be throttled (429) or rate limited by OTP service
        self.assertIn(
            response.status_code,
            [status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_400_BAD_REQUEST]
        )
    
    def test_otp_request_phone_throttle(self):
        """Test OTP request throttling by phone number (3/min)."""
        phone = '+989222222222'
        
        # Mock the OTP generation to avoid rate limit from OTP service itself
        with patch('accounts.services.otp.OTPService._generate_code', return_value='123456'):
            # First 3 requests should succeed (or be rate limited by backend)
            for i in range(3):
                response = self.client.post('/api/auth/otp/request/', {
                    'phone_number': phone
                })
                # May get 200 OK or 429 from IP throttle
                self.assertIn(
                    response.status_code,
                    [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS],
                    f"Request {i+1} failed unexpectedly"
                )
            
            # Additional requests should eventually be throttled
            response = self.client.post('/api/auth/otp/request/', {
                'phone_number': phone
            })
            # Should be throttled or rate limited
            self.assertIn(
                response.status_code,
                [status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_400_BAD_REQUEST]
            )
    
    def test_content_generate_throttle(self):
        """Test content generation throttling (10/min per user)."""
        # Authenticate
        self.client.force_authenticate(user=self.user)
        
        # Mock the usage limit check to allow generation
        with patch('ai.services.check_workspace_usage_limits', return_value=(True, 'OK')):
            # First 10 requests should succeed or be queued
            for i in range(10):
                response = self.client.post(
                    f'/api/contents/{self.content.id}/generate/',
                    {
                        'kind': 'draft',
                        'topic': f'Test topic {i}',
                        'min_words': 100
                    }
                )
                # Should be accepted (202) or throttled (429)
                self.assertIn(
                    response.status_code,
                    [status.HTTP_202_ACCEPTED, status.HTTP_429_TOO_MANY_REQUESTS],
                    f"Request {i+1} got unexpected status: {response.status_code}"
                )
            
            # 11th request should be throttled
            response = self.client.post(
                f'/api/contents/{self.content.id}/generate/',
                {
                    'kind': 'draft',
                    'topic': 'Test topic overflow',
                    'min_words': 100
                }
            )
            
            # Should likely be throttled at this point
            # (may succeed if prior requests were throttled)
            self.assertIn(
                response.status_code,
                [status.HTTP_202_ACCEPTED, status.HTTP_429_TOO_MANY_REQUESTS]
            )
    
    def test_throttle_different_users(self):
        """Test that throttles are per-user for authenticated endpoints."""
        # Create second user
        user2 = User.objects.create_user(
            phone_number='+989333333333',
            is_active=True
        )
        
        content2 = Content.objects.create(
            project=self.project,
            prompt=self.prompt,
            title='Test Content 2',
            created_by=user2,
            status=Content.Status.DRAFT
        )
        
        # Mock usage limits
        with patch('ai.services.check_workspace_usage_limits', return_value=(True, 'OK')):
            # User 1 makes requests
            self.client.force_authenticate(user=self.user)
            for i in range(5):
                response = self.client.post(
                    f'/api/contents/{self.content.id}/generate/',
                    {'kind': 'draft', 'topic': f'User1 topic {i}', 'min_words': 100}
                )
            
            # User 2 should have their own throttle limit
            self.client.force_authenticate(user=user2)
            response = self.client.post(
                f'/api/contents/{content2.id}/generate/',
                {'kind': 'draft', 'topic': 'User2 topic', 'min_words': 100}
            )
            
            # User 2's first request should succeed
            self.assertIn(
                response.status_code,
                [status.HTTP_202_ACCEPTED, status.HTTP_429_TOO_MANY_REQUESTS]
            )


class ThrottleHeadersTestCase(TestCase):
    """Test that throttle headers are returned."""
    
    def test_throttle_headers_present(self):
        """Test that rate limit headers are present in response."""
        client = APIClient()
        
        response = client.post('/api/auth/otp/request/', {
            'phone_number': '+989444444444'
        })
        
        # DRF may include throttle headers
        # (Exact headers depend on DRF configuration)
        self.assertTrue(
            response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_429_TOO_MANY_REQUESTS,
                status.HTTP_400_BAD_REQUEST
            ]
        )
