"""
Celery tasks for AI app.
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task
def monthly_usage_reset():
    """
    Reset monthly usage counters.
    Runs on the first day of each month.
    """
    from ai.models import UsageLog
    
    # This is a placeholder - actual implementation would depend on
    # whether we track cumulative usage or reset limits
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    
    logger.info(f"Monthly usage reset executed for {current_month}")
    return True


@shared_task
def log_usage_task(content_id, user_id, workspace_id, organization_id,
                   model, prompt_tokens, completion_tokens, 
                   total_tokens, estimated_cost, request_duration=None,
                   success=True, error_message=None):
    """
    Log OpenAI API usage asynchronously.
    
    Args:
        content_id: Content ID
        user_id: User ID
        workspace_id: Workspace ID
        organization_id: Organization ID
        model: OpenAI model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        total_tokens: Total tokens
        estimated_cost: Estimated cost in USD
        request_duration: Request duration in seconds
        success: Whether request was successful
        error_message: Error message if failed
    """
    from ai.models import UsageLog
    
    try:
        log = UsageLog.objects.create(
            content_id=content_id,
            user_id=user_id,
            workspace_id=workspace_id,
            organization_id=organization_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=Decimal(str(estimated_cost)),
            request_duration=Decimal(str(request_duration)) if request_duration else None,
            success=success,
            error_message=error_message
        )
        
        logger.info(f"Usage logged: {log.id} - {total_tokens} tokens")
        return log.id
        
    except Exception as e:
        logger.error(f"Failed to log usage: {str(e)}")
        raise


@shared_task
def check_usage_limits(scope, scope_id, current_usage):
    """
    Check if usage exceeds limits.
    
    Args:
        scope: 'user', 'workspace', or 'organization'
        scope_id: ID of the scope entity
        current_usage: Dict with usage stats
    
    Returns:
        Dict with exceeded status and limits
    """
    from ai.models import UsageLimit
    
    try:
        limit = UsageLimit.objects.get(scope=scope, scope_id=scope_id)
        
        exceeded = {}
        
        if limit.requests_limit and current_usage.get('requests', 0) >= limit.requests_limit:
            exceeded['requests'] = {
                'limit': limit.requests_limit,
                'current': current_usage['requests']
            }
        
        if limit.tokens_limit and current_usage.get('tokens', 0) >= limit.tokens_limit:
            exceeded['tokens'] = {
                'limit': limit.tokens_limit,
                'current': current_usage['tokens']
            }
        
        if limit.cost_limit and current_usage.get('cost', 0) >= float(limit.cost_limit):
            exceeded['cost'] = {
                'limit': float(limit.cost_limit),
                'current': current_usage['cost']
            }
        
        return {
            'exceeded': bool(exceeded),
            'limits': exceeded
        }
        
    except UsageLimit.DoesNotExist:
        # No limits set
        return {'exceeded': False, 'limits': {}}
    except Exception as e:
        logger.error(f"Failed to check usage limits: {str(e)}")
        raise
