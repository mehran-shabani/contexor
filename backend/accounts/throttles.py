"""
Custom throttle classes for rate limiting.
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class OTPRequestIPThrottle(AnonRateThrottle):
    """
    Throttle OTP requests by IP address.
    Limit: 5 requests per minute per IP.
    """
    scope = 'otp_request_ip'
    
    def get_cache_key(self, request, view):
        # Only apply to OTP request endpoint
        if request.path.endswith('/auth/otp/request/') or request.path.endswith('/auth/otp/request'):
            return self.cache_format % {
                'scope': self.scope,
                'ident': self.get_ident(request)
            }
        return None


class OTPRequestPhoneThrottle(AnonRateThrottle):
    """
    Throttle OTP requests by phone number.
    Limit: 3 requests per minute per phone number.
    """
    scope = 'otp_request_phone'
    
    def get_cache_key(self, request, view):
        # Only apply to OTP request endpoint
        if request.path.endswith('/auth/otp/request/') or request.path.endswith('/auth/otp/request'):
            phone_number = request.data.get('phone_number')
            if phone_number:
                return self.cache_format % {
                    'scope': self.scope,
                    'ident': phone_number
                }
        return None


class ContentGenerateThrottle(UserRateThrottle):
    """
    Throttle content generation requests.
    Limit: 10 requests per minute per user.
    """
    scope = 'content_generate'
    
    def get_cache_key(self, request, view):
        # Only apply to generate endpoints
        if '/generate' in request.path and request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk
            }
        return None
