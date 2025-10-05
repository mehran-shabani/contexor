"""
Core views for health checks and monitoring.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint for Docker healthcheck.
    Returns 200 if all services are healthy.
    """
    health_status = {
        'status': 'healthy',
        'services': {}
    }
    
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['services']['database'] = 'ok'
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status['services']['database'] = 'error'
        health_status['status'] = 'unhealthy'
    
    try:
        # Check cache/redis
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['services']['cache'] = 'ok'
        else:
            health_status['services']['cache'] = 'error'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        health_status['services']['cache'] = 'error'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
