"""
SMS service using Kavenegar.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_sms(phone_number: str, code: str) -> bool:
    """
    Send OTP code via SMS using Kavenegar.
    
    Args:
        phone_number: Recipient phone number
        code: OTP code to send
        
    Returns:
        True if sent successfully
        
    Raises:
        Exception: If SMS sending fails
    """
    # Mock SMS in development/testing
    if getattr(settings, 'MOCK_SMS', False):
        logger.info(f"[MOCK SMS] Sending OTP {code} to {phone_number}")
        return True
    
    try:
        from kavenegar import KavenegarAPI, APIException, HTTPException
        
        api_key = getattr(settings, 'KAVENEGAR_API_KEY', '')
        if not api_key:
            raise ValueError("KAVENEGAR_API_KEY not configured")
        
        api = KavenegarAPI(api_key)
        
        # Get template and sender from settings
        template = getattr(settings, 'KAVENEGAR_TEMPLATE', 'login-otp')
        sender = getattr(settings, 'KAVENEGAR_SENDER', '')
        
        # Send verification lookup
        params = {
            'receptor': phone_number,
            'template': template,
            'token': code,
            'type': 'sms',
        }
        
        response = api.verify_lookup(params)
        
        logger.info(f"OTP sent to {phone_number} via Kavenegar")
        return True
        
    except APIException as e:
        logger.error(f"Kavenegar API error: {e}")
        raise Exception(f"SMS API error: {e}")
    except HTTPException as e:
        logger.error(f"Kavenegar HTTP error: {e}")
        raise Exception(f"SMS HTTP error: {e}")
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise
