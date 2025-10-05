"""
Services for AI operations including usage limits and content generation.
"""
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
import logging

from .models import UsageLog, UsageLimit
from accounts.models import Workspace

logger = logging.getLogger(__name__)


def check_workspace_usage_limits(workspace):
    """
    Check if workspace has exceeded usage limits.
    
    Args:
        workspace: Workspace instance
        
    Returns:
        Tuple of (bool, str) - (limits_ok, message)
    """
    # Get current month's usage
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Check for configured limits
    try:
        limit = UsageLimit.objects.get(
            scope=UsageLimit.Scope.WORKSPACE,
            scope_id=workspace.id
        )
        has_custom_limit = True
    except UsageLimit.DoesNotExist:
        # Use default budget from settings
        has_custom_limit = False
        limit = None
    
    # Determine start date based on period
    if has_custom_limit:
        if limit.period == UsageLimit.Period.MONTHLY:
            start_date = start_of_month
        else:  # DAILY
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Default to monthly
        start_date = start_of_month
    
    # Aggregate usage
    usage = UsageLog.objects.filter(
        workspace=workspace,
        timestamp__gte=start_date,
        success=True
    ).aggregate(
        total_requests=Sum('id'),
        total_tokens=Sum('total_tokens'),
        total_cost=Sum('estimated_cost')
    )
    
    current_requests = UsageLog.objects.filter(
        workspace=workspace,
        timestamp__gte=start_date
    ).count()
    
    current_tokens = usage['total_tokens'] or 0
    current_cost = float(usage['total_cost'] or 0)
    
    # Check limits
    if has_custom_limit:
        # Check custom configured limits
        if limit.requests_limit and current_requests >= limit.requests_limit:
            return False, f"Request limit exceeded: {current_requests}/{limit.requests_limit}"
        
        if limit.tokens_limit and current_tokens >= limit.tokens_limit:
            return False, f"Token limit exceeded: {current_tokens}/{limit.tokens_limit}"
        
        if limit.cost_limit and current_cost >= float(limit.cost_limit):
            return False, f"Monthly budget exceeded: ${current_cost:.2f}/${limit.cost_limit}"
    else:
        # Check default budget from settings
        workspace_budget = getattr(settings, 'AI_WORKSPACE_MONTHLY_BUDGET_USD', 100.0)
        if current_cost >= workspace_budget:
            return False, f"Monthly budget exceeded: ${current_cost:.2f}/${workspace_budget:.2f}. Please upgrade your plan or wait until next month."
    
    return True, "Within limits"


def check_user_usage_limits(user):
    """
    Check if user has exceeded usage limits.
    
    Args:
        user: User instance
        
    Returns:
        Tuple of (bool, str) - (limits_ok, message)
    """
    # Get current month's usage
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Check for configured limits
    try:
        limit = UsageLimit.objects.get(
            scope=UsageLimit.Scope.USER,
            scope_id=user.id
        )
        has_custom_limit = True
    except UsageLimit.DoesNotExist:
        # Use default budget from settings
        has_custom_limit = False
        limit = None
    
    # Determine start date
    if has_custom_limit:
        if limit.period == UsageLimit.Period.MONTHLY:
            start_date = start_of_month
        else:  # DAILY
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Default to monthly
        start_date = start_of_month
    
    # Aggregate usage
    usage = UsageLog.objects.filter(
        user=user,
        timestamp__gte=start_date,
        success=True
    ).aggregate(
        total_cost=Sum('estimated_cost')
    )
    
    current_cost = float(usage['total_cost'] or 0)
    
    # Check limits
    if has_custom_limit and limit.cost_limit:
        if current_cost >= float(limit.cost_limit):
            return False, f"User monthly budget exceeded: ${current_cost:.2f}/${limit.cost_limit}"
    else:
        # Check default user budget
        user_budget = getattr(settings, 'AI_USER_MONTHLY_BUDGET_USD', 50.0)
        if current_cost >= user_budget:
            return False, f"User monthly budget exceeded: ${current_cost:.2f}/${user_budget:.2f}"
    
    return True, "Within limits"


def get_usage_summary(workspace=None, user=None, organization=None, start_date=None, end_date=None):
    """
    Get usage summary for a given scope.
    
    Args:
        workspace: Optional Workspace instance
        user: Optional User instance
        organization: Optional Organization instance
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        Dict with usage statistics
    """
    queryset = UsageLog.objects.filter(success=True)
    
    if workspace:
        queryset = queryset.filter(workspace=workspace)
    if user:
        queryset = queryset.filter(user=user)
    if organization:
        queryset = queryset.filter(organization=organization)
    
    if start_date:
        queryset = queryset.filter(timestamp__gte=start_date)
    if end_date:
        queryset = queryset.filter(timestamp__lte=end_date)
    
    # Aggregate
    summary = queryset.aggregate(
        total_requests=Sum('id'),
        total_prompt_tokens=Sum('prompt_tokens'),
        total_completion_tokens=Sum('completion_tokens'),
        total_tokens=Sum('total_tokens'),
        total_cost=Sum('estimated_cost')
    )
    
    request_count = queryset.count()
    
    # Model breakdown
    model_breakdown = {}
    for log in queryset.values('model').annotate(
        count=Sum('id'),
        tokens=Sum('total_tokens'),
        cost=Sum('estimated_cost')
    ):
        model_breakdown[log['model']] = {
            'requests': queryset.filter(model=log['model']).count(),
            'tokens': log['tokens'] or 0,
            'cost': float(log['cost'] or 0)
        }
    
    return {
        'total_requests': request_count,
        'total_prompt_tokens': summary['total_prompt_tokens'] or 0,
        'total_completion_tokens': summary['total_completion_tokens'] or 0,
        'total_tokens': summary['total_tokens'] or 0,
        'total_cost': float(summary['total_cost'] or 0),
        'model_breakdown': model_breakdown
    }


def log_ai_usage(content=None, ai_job=None, user=None, workspace=None, organization=None,
                 model=None, prompt_tokens=0, completion_tokens=0, 
                 total_tokens=0, estimated_cost=0.0, request_duration=None,
                 success=True, error_message=None):
    """
    Log AI usage synchronously.
    
    Args:
        content: Content instance
        ai_job: AiJob instance
        user: User instance
        workspace: Workspace instance
        organization: Organization instance
        model: Model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        total_tokens: Total tokens
        estimated_cost: Estimated cost in USD
        request_duration: Request duration in seconds
        success: Whether request was successful
        error_message: Error message if failed
        
    Returns:
        UsageLog instance
    """
    try:
        log = UsageLog.objects.create(
            content=content,
            ai_job=ai_job,
            user=user,
            workspace=workspace,
            organization=organization,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=Decimal(str(estimated_cost)),
            request_duration=Decimal(str(request_duration)) if request_duration else None,
            success=success,
            error_message=error_message
        )
        
        logger.info(f"Usage logged: {log.id} - {total_tokens} tokens - ${estimated_cost:.6f}")
        return log
        
    except Exception as e:
        logger.error(f"Failed to log usage: {str(e)}")
        raise


# Default settings for usage limits
DEFAULT_MONTHLY_TOKEN_LIMIT = getattr(settings, 'DEFAULT_MONTHLY_TOKEN_LIMIT', 1_000_000)
DEFAULT_MONTHLY_COST_LIMIT = getattr(settings, 'DEFAULT_MONTHLY_COST_LIMIT', 100.0)
DEFAULT_MONTHLY_REQUEST_LIMIT = getattr(settings, 'DEFAULT_MONTHLY_REQUEST_LIMIT', 1000)
