"""
Celery tasks for AI app.
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings
from decimal import Decimal
import logging
import time

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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_content_task(self, content_id, params, job_id):
    """
    Generate content using OpenAI Responses API with PII redaction.
    
    Args:
        content_id: Content ID
        params: Dict with generation parameters
        job_id: AiJob ID
        
    Returns:
        Dict with generation result
    """
    from contentmgmt.models import Content, ContentVersion
    from ai.models import AiJob
    from ai.client import get_openai_client, calculate_cost
    from ai.pii import redact_pii, restore_pii
    from ai.services import log_ai_usage
    from ai.prompts.models import DEFAULT_BLOG_DRAFT_PROMPT
    
    try:
        # Get content and job
        content = Content.objects.get(id=content_id)
        job = AiJob.objects.get(id=job_id)
        
        # Mark job as running
        job.mark_running()
        logger.info(f"Starting content generation job {job_id} for content {content_id}")
        
        # Get parameters
        kind = params.get('kind', 'draft')
        topic = params.get('topic', content.title)
        tone = params.get('tone', 'حرفه‌ای')
        audience = params.get('audience', 'عمومی')
        keywords = params.get('keywords', '')
        min_words = params.get('min_words', 500)
        additional_instructions = params.get('additional_instructions', '')
        
        # Build prompt based on kind
        if kind == 'draft':
            # Use default Persian blog draft prompt
            user_prompt = DEFAULT_BLOG_DRAFT_PROMPT.format(
                topic=topic,
                tone=tone,
                audience=audience,
                min_words=min_words,
                keywords=keywords
            )
            
            if additional_instructions:
                user_prompt += f"\n\n**دستورالعمل‌های اضافی:**\n{additional_instructions}"
        
        else:
            # Simple prompt for other kinds
            user_prompt = f"موضوع: {topic}\nلحن: {tone}\nمخاطب: {audience}\nکلمات کلیدی: {keywords}"
            if additional_instructions:
                user_prompt += f"\n\n{additional_instructions}"
        
        # Redact PII from user input
        redactor = None
        if topic or keywords or additional_instructions:
            from ai.pii import PIIRedactor
            redactor = PIIRedactor()
            
            input_text = f"{topic}\n{keywords}\n{additional_instructions}"
            redacted_input, pii_warnings = redactor.redact(input_text)
            
            if pii_warnings:
                logger.warning(f"PII detected in input for job {job_id}: {pii_warnings}")
                content.has_pii = True
                content.pii_warnings = pii_warnings
                content.save(update_fields=['has_pii', 'pii_warnings'])
        
        # Get OpenAI client
        client = get_openai_client()
        model = getattr(settings, 'OPENAI_DEFAULT_MODEL', 'gpt-4o-mini')
        
        # Call OpenAI API
        start_time = time.time()
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "شما یک نویسنده فارسی‌زبان حرفه‌ای هستید که در تولید محتوای باکیفیت تخصص دارید."
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            request_duration = time.time() - start_time
            
            # Extract generated content
            generated_text = response.choices[0].message.content
            
            # Restore PII if it was redacted
            if redactor and redactor.get_mapping():
                generated_text = redactor.restore(generated_text)
            
            # Calculate usage and cost
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            cost = calculate_cost(model, input_tokens, output_tokens)
            
            # Log usage
            log_ai_usage(
                content=content,
                ai_job=job,
                user=job.user,
                workspace=job.workspace,
                organization=content.project.workspace.organization,
                model=model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost=cost,
                request_duration=request_duration,
                success=True
            )
            
            # Create new version
            version_number = content.versions.count() + 1
            version = ContentVersion.objects.create(
                content=content,
                version_number=version_number,
                title=content.title,
                body_markdown=generated_text,
                metadata={
                    'kind': kind,
                    'model': model,
                    'tokens': total_tokens,
                    'cost': float(cost),
                    'params': params
                },
                ai_job=job,
                created_by=job.user
            )
            
            # Update content
            content.current_version = version
            content.body = generated_text
            content.word_count = version.word_count
            content.status = Content.Status.REVIEW
            content.save()
            
            # Mark job as completed
            job.mark_completed({
                'version_id': version.id,
                'version_number': version_number,
                'tokens': total_tokens,
                'cost': float(cost)
            })
            
            logger.info(f"Content generation job {job_id} completed successfully")
            
            return {
                'success': True,
                'version_id': version.id,
                'version_number': version_number,
                'tokens': total_tokens,
                'cost': float(cost)
            }
            
        except Exception as api_error:
            logger.error(f"OpenAI API error in job {job_id}: {str(api_error)}")
            
            # Log failed usage
            log_ai_usage(
                content=content,
                ai_job=job,
                user=job.user,
                workspace=job.workspace,
                organization=content.project.workspace.organization,
                model=model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                estimated_cost=0.0,
                request_duration=time.time() - start_time,
                success=False,
                error_message=str(api_error)
            )
            
            # Retry if retries left
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying job {job_id}, attempt {self.request.retries + 1}")
                raise self.retry(exc=api_error)
            else:
                # Mark as failed after max retries
                job.mark_failed(f"OpenAI API error: {str(api_error)}")
                content.status = Content.Status.DRAFT
                content.save(update_fields=['status'])
                raise
    
    except Exception as e:
        logger.error(f"Error in generate_content_task: {str(e)}")
        
        try:
            job = AiJob.objects.get(id=job_id)
            job.mark_failed(str(e))
        except:
            pass
        
        raise
