"""
Celery tasks for accounts app.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_otps():
    """
    Clean up expired OTP codes.
    Runs every 10 minutes via Celery Beat.
    """
    from accounts.models import OTPCode
    
    # Delete OTPs that expired more than 1 hour ago
    cutoff = timezone.now() - timezone.timedelta(hours=1)
    deleted_count, _ = OTPCode.objects.filter(expires_at__lt=cutoff).delete()
    
    logger.info(f"Cleaned up {deleted_count} expired OTP codes")
    return deleted_count


@shared_task
def send_otp_sms_task(phone_number: str, code: str):
    """
    Send OTP SMS asynchronously.
    
    Args:
        phone_number: Recipient phone number
        code: OTP code
    """
    from accounts.services.sms import send_otp_sms
    
    try:
        send_otp_sms(phone_number, code)
        logger.info(f"OTP SMS sent to {phone_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP SMS to {phone_number}: {str(e)}")
        raise
