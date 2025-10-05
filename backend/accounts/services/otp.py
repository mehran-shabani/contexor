"""
OTP Service with PBKDF2 hashing and rate limiting.
"""
import hashlib
import random
import logging
from datetime import timedelta
from typing import Tuple, Optional

from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from accounts.models import OTPCode, User
from accounts.services.sms import send_otp_sms

logger = logging.getLogger(__name__)


class OTPService:
    """Service for managing OTP codes."""
    
    # Constants
    OTP_LENGTH = 6
    HASH_ITERATIONS = 100000
    HASH_ALGORITHM = 'sha256'
    
    @staticmethod
    def _hash_code(code: str) -> str:
        """
        Hash OTP code using PBKDF2.
        
        Args:
            code: The OTP code to hash
            
        Returns:
            Hashed code
        """
        # Use Django's SECRET_KEY as salt
        salt = settings.SECRET_KEY.encode()
        hash_obj = hashlib.pbkdf2_hmac(
            OTPService.HASH_ALGORITHM,
            code.encode(),
            salt,
            OTPService.HASH_ITERATIONS
        )
        return hash_obj.hex()
    
    @staticmethod
    def _verify_hash(code: str, code_hash: str) -> bool:
        """
        Verify OTP code against hash.
        
        Args:
            code: The plain OTP code
            code_hash: The stored hash
            
        Returns:
            True if code matches hash
        """
        return OTPService._hash_code(code) == code_hash
    
    @staticmethod
    def _generate_code() -> str:
        """
        Generate a random 6-digit OTP code.
        
        Returns:
            6-digit code as string
        """
        return ''.join([str(random.randint(0, 9)) for _ in range(OTPService.OTP_LENGTH)])
    
    @staticmethod
    def _check_rate_limit(phone_number: str) -> Tuple[bool, Optional[int]]:
        """
        Check if phone number is rate limited.
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            Tuple of (is_allowed, seconds_until_next_attempt)
        """
        cache_key = f'otp_rate_limit:{phone_number}'
        last_request = cache.get(cache_key)
        
        if last_request:
            rate_limit = getattr(settings, 'OTP_RATE_LIMIT', 60)
            elapsed = (timezone.now() - last_request).total_seconds()
            if elapsed < rate_limit:
                return False, int(rate_limit - elapsed)
        
        return True, None
    
    @staticmethod
    def _set_rate_limit(phone_number: str):
        """
        Set rate limit for phone number.
        
        Args:
            phone_number: Phone number to rate limit
        """
        cache_key = f'otp_rate_limit:{phone_number}'
        rate_limit = getattr(settings, 'OTP_RATE_LIMIT', 60)
        cache.set(cache_key, timezone.now(), rate_limit)
    
    @staticmethod
    def issue_otp(phone_number: str) -> Tuple[bool, str, Optional[int]]:
        """
        Issue a new OTP code for phone number.
        
        Args:
            phone_number: Phone number to send OTP to
            
        Returns:
            Tuple of (success, message, ttl_seconds)
        """
        # Check rate limit
        is_allowed, wait_time = OTPService._check_rate_limit(phone_number)
        if not is_allowed:
            return False, f'Please wait {wait_time} seconds before requesting another code', wait_time
        
        # Generate new code
        code = OTPService._generate_code()
        code_hash = OTPService._hash_code(code)
        
        # Set expiration
        ttl = getattr(settings, 'OTP_TTL', 300)  # 5 minutes default
        expires_at = timezone.now() + timedelta(seconds=ttl)
        
        # Invalidate previous OTP codes for this phone number
        OTPCode.objects.filter(
            phone_number=phone_number,
            is_used=False
        ).update(is_used=True)
        
        # Create new OTP code
        otp = OTPCode.objects.create(
            phone_number=phone_number,
            code_hash=code_hash,
            expires_at=expires_at
        )
        
        # Send SMS
        try:
            send_otp_sms(phone_number, code)
            logger.info(f"OTP sent to {phone_number}")
        except Exception as e:
            logger.error(f"Failed to send OTP to {phone_number}: {str(e)}")
            # Continue even if SMS fails (for testing)
            if not getattr(settings, 'MOCK_SMS', False):
                return False, 'Failed to send SMS', None
        
        # Set rate limit
        OTPService._set_rate_limit(phone_number)
        
        # Log code for development (remove in production)
        if settings.DEBUG or getattr(settings, 'MOCK_SMS', False):
            logger.info(f"OTP code for {phone_number}: {code}")
        
        return True, 'OTP sent successfully', ttl
    
    @staticmethod
    def verify_otp(phone_number: str, code: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Verify OTP code and create/login user.
        
        Args:
            phone_number: Phone number
            code: OTP code to verify
            
        Returns:
            Tuple of (success, message, token_data)
            token_data contains: {
                'access': access_token,
                'refresh': refresh_token,
                'user': user_data
            }
        """
        # Find valid OTP
        otp = OTPCode.objects.filter(
            phone_number=phone_number,
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()
        
        if not otp:
            return False, 'Invalid or expired OTP code', None
        
        # Check attempt count
        if not otp.can_attempt():
            otp.is_used = True
            otp.save()
            return False, 'Too many failed attempts', None
        
        # Verify code
        if not OTPService._verify_hash(code, otp.code_hash):
            otp.attempt_count += 1
            otp.save()
            remaining = getattr(settings, 'OTP_MAX_ATTEMPTS', 5) - otp.attempt_count
            return False, f'Invalid code. {remaining} attempts remaining', None
        
        # Mark OTP as used
        otp.is_used = True
        otp.save()
        
        # Create or get user
        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={'is_active': True}
        )
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        token_data = {
            'access': str(access),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'full_name': user.full_name,
                'email': user.email,
            }
        }
        
        action = 'registered' if created else 'logged in'
        logger.info(f"User {phone_number} {action} successfully")
        
        return True, f'Successfully {action}', token_data
