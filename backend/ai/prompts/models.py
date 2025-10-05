"""
Prompt templates for AI content generation.
"""
from django.db import models
from django.conf import settings
from accounts.models import Workspace


class PromptKind(models.TextChoices):
    """Enumeration of prompt kinds."""
    OUTLINE = 'outline', 'Outline'
    DRAFT = 'draft', 'Draft'
    REWRITE = 'rewrite', 'Rewrite'
    CAPTION = 'caption', 'Caption'


class PromptTemplate(models.Model):
    """
    Reusable prompt templates with versioning.
    """
    
    title = models.CharField(max_length=255)
    kind = models.CharField(
        max_length=20,
        choices=PromptKind.choices,
        help_text='Type of content generation'
    )
    template_text = models.TextField(
        help_text='Prompt template with {placeholders}'
    )
    params = models.JSONField(
        default=dict,
        help_text='Parameter definitions and defaults'
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prompt_templates',
        help_text='If null, template is global'
    )
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_prompt_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prompt_templates'
        indexes = [
            models.Index(fields=['kind']),
            models.Index(fields=['workspace']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-usage_count']),
        ]
        ordering = ['-usage_count', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_kind_display()}) v{self.version}"
    
    def increment_usage(self):
        """Increment usage counter."""
        self.usage_count = models.F('usage_count') + 1
        self.save(update_fields=['usage_count'])


# Default Persian blog draft prompt
DEFAULT_BLOG_DRAFT_PROMPT = """شما یک نویسنده فارسی‌زبان حرفه‌ای هستید که در تولید محتوای وبلاگ با کیفیت بالا تخصص دارید.

وظیفه شما نوشتن یک مقاله وبلاگ کامل و جذاب به زبان فارسی است که:

**موضوع:** {topic}
**لحن:** {tone}
**مخاطب:** {audience}
**حداقل تعداد کلمات:** {min_words}
**کلمات کلیدی:** {keywords}

**الزامات:**
1. مقدمه جذاب که توجه خواننده را جلب کند
2. حداقل 3 بخش اصلی با عناوین H2 مناسب
3. استفاده از زیرعناوین H3 در صورت نیاز
4. محتوا باید ساختاریافته و خوانا باشد
5. جمع‌بندی قوی با فراخوان به اقدام (CTA)
6. یک متادیسکریپشن فارسی 150-160 کاراکتری در انتها

**قالب خروجی (Markdown):**

# {عنوان اصلی}

{مقدمه}

## بخش اول

{محتوا}

### زیرعنوان (اختیاری)

{محتوا}

## بخش دوم

{محتوا}

## بخش سوم

{محتوا}

## نتیجه‌گیری

{جمع‌بندی و CTA}

---

**متادیسکریپشن:** {متادیسکریپشن فارسی}

**نکات مهم:**
- از زبان فارسی استانداد و روان استفاده کنید
- محتوا باید SEO-friendly باشد
- از کلمات کلیدی به صورت طبیعی استفاده کنید
- محتوا باید ارزش‌آفرین و مفید باشد
- راست‌چین (RTL) بنویسید
"""
