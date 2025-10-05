"""
Unit tests for OTP service.
"""
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from accounts.models import OTPCode, User
from accounts.services.otp import OTPService


@override_settings(
    MOCK_SMS=True,
    OTP_TTL=300,
    OTP_MAX_ATTEMPTS=5,
    OTP_RATE_LIMIT=60
)
class OTPServiceTestCase(TestCase):
    """Test cases for OTP service."""
    
    def setUp(self):
        """Set up test data."""
        self.phone_number = '+989123456789'
    
    def test_issue_otp_success(self):
        """Test successful OTP issuance."""
        success, message, ttl = OTPService.issue_otp(self.phone_number)
        
        self.assertTrue(success)
        self.assertEqual(ttl, 300)
        
        # Verify OTP was created
        otp = OTPCode.objects.filter(phone_number=self.phone_number, is_used=False).first()
        self.assertIsNotNone(otp)
        self.assertFalse(otp.is_used)
        self.assertEqual(otp.attempt_count, 0)
    
    def test_issue_otp_rate_limit(self):
        """Test OTP rate limiting."""
        # First request should succeed
        success1, _, _ = OTPService.issue_otp(self.phone_number)
        self.assertTrue(success1)
        
        # Second immediate request should fail
        success2, message, wait_time = OTPService.issue_otp(self.phone_number)
        self.assertFalse(success2)
        self.assertIsNotNone(wait_time)
        self.assertIn('wait', message.lower())
    
    def test_issue_otp_invalidates_previous(self):
        """Test that new OTP invalidates previous ones."""
        # Issue first OTP
        OTPService.issue_otp(self.phone_number)
        first_otp = OTPCode.objects.filter(phone_number=self.phone_number).first()
        
        # Clear rate limit cache for test
        from django.core.cache import cache
        cache.delete(f'otp_rate_limit:{self.phone_number}')
        
        # Issue second OTP
        OTPService.issue_otp(self.phone_number)
        
        # First OTP should be marked as used
        first_otp.refresh_from_db()
        self.assertTrue(first_otp.is_used)
    
    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        # Issue OTP and capture the code
        with patch('accounts.services.otp.OTPService._generate_code', return_value='123456'):
            OTPService.issue_otp(self.phone_number)
        
        # Verify OTP
        success, message, token_data = OTPService.verify_otp(self.phone_number, '123456')
        
        self.assertTrue(success)
        self.assertIsNotNone(token_data)
        self.assertIn('access', token_data)
        self.assertIn('refresh', token_data)
        self.assertIn('user', token_data)
        
        # Verify user was created
        user = User.objects.filter(phone_number=self.phone_number).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)
    
    def test_verify_otp_invalid_code(self):
        """Test OTP verification with invalid code."""
        # Issue OTP
        with patch('accounts.services.otp.OTPService._generate_code', return_value='123456'):
            OTPService.issue_otp(self.phone_number)
        
        # Try to verify with wrong code
        success, message, token_data = OTPService.verify_otp(self.phone_number, '999999')
        
        self.assertFalse(success)
        self.assertIsNone(token_data)
        self.assertIn('invalid', message.lower())
        
        # Check attempt count increased
        otp = OTPCode.objects.filter(phone_number=self.phone_number, is_used=False).first()
        self.assertEqual(otp.attempt_count, 1)
    
    def test_verify_otp_max_attempts(self):
        """Test OTP verification with max attempts exceeded."""
        # Issue OTP
        with patch('accounts.services.otp.OTPService._generate_code', return_value='123456'):
            OTPService.issue_otp(self.phone_number)
        
        # Try wrong code 5 times
        for i in range(5):
            success, _, _ = OTPService.verify_otp(self.phone_number, '999999')
            self.assertFalse(success)
        
        # 6th attempt should fail due to max attempts
        success, message, _ = OTPService.verify_otp(self.phone_number, '123456')
        self.assertFalse(success)
        
        # OTP should be marked as used
        otp = OTPCode.objects.filter(phone_number=self.phone_number).first()
        self.assertTrue(otp.is_used)
    
    def test_verify_otp_expired(self):
        """Test OTP verification with expired code."""
        # Create expired OTP
        with patch('accounts.services.otp.OTPService._generate_code', return_value='123456'):
            OTPService.issue_otp(self.phone_number)
        
        # Manually set expiration to past
        otp = OTPCode.objects.filter(phone_number=self.phone_number, is_used=False).first()
        otp.expires_at = timezone.now() - timedelta(seconds=1)
        otp.save()
        
        # Try to verify
        success, message, token_data = OTPService.verify_otp(self.phone_number, '123456')
        
        self.assertFalse(success)
        self.assertIsNone(token_data)
        self.assertIn('expired', message.lower())
    
    def test_verify_otp_no_code_issued(self):
        """Test OTP verification without issuing code first."""
        success, message, token_data = OTPService.verify_otp(self.phone_number, '123456')
        
        self.assertFalse(success)
        self.assertIsNone(token_data)
        self.assertIn('invalid', message.lower())
    
    def test_hash_code(self):
        """Test OTP code hashing."""
        code = '123456'
        hash1 = OTPService._hash_code(code)
        hash2 = OTPService._hash_code(code)
        
        # Same code should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Hash should be different from original code
        self.assertNotEqual(hash1, code)
        
        # Different code should produce different hash
        hash3 = OTPService._hash_code('654321')
        self.assertNotEqual(hash1, hash3)
    
    def test_verify_hash(self):
        """Test hash verification."""
        code = '123456'
        code_hash = OTPService._hash_code(code)
        
        # Correct code should verify
        self.assertTrue(OTPService._verify_hash(code, code_hash))
        
        # Wrong code should not verify
        self.assertFalse(OTPService._verify_hash('999999', code_hash))
