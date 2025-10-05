# خلاصه پیاده‌سازی پرامپت 3 - AI Agent، Jobs، و Usage Tracking

## ✅ وظایف انجام شده

### 1. ماژول backend/ai/

#### client.py
```python
✅ کلاس OpenAIClient (Singleton pattern)
✅ راه‌اندازی OpenAI با api_key و base_url از env
✅ محاسبه هزینه (pricing برای تمام مدل‌ها)
✅ Helper functions: get_openai_client(), calculate_cost()
```

#### pii.py
```python
✅ کلاس PIIRedactor
✅ Regex patterns:
   - تلفن ایران: (?:\+?98|0)?9\d{9}
   - ایمیل: RFC 5322 simplified
   - IBAN ایران: IR[0-9]{24}
   - کد ملی: \b\d{10}\b (اختیاری)
✅ متدهای redact() و restore()
✅ نگه‌داری map امن در حافظه job
✅ Helper functions: redact_pii(), restore_pii()
```

#### prompts/models.py
```python
✅ مدل PromptTemplate:
   - kind ENUM: outline, draft, rewrite, caption
   - template_text با placeholders
   - params jsonb
   - version و is_active
   - workspace (nullable برای global templates)
✅ پرامپت فارسی پیش‌فرض برای blog draft
   - ساختار: مقدمه، H2/H3، جمع‌بندی، متادیسکریپشن
   - پارامترهای: topic, tone, audience, min_words, keywords
```

### 2. مدل‌های جدید

#### ai/models.py
```python
✅ AiJob:
   - content FK, user FK, workspace FK
   - status: pending/running/completed/failed/cancelled
   - kind, params jsonb, result_data jsonb
   - retry_count (حداکثر 3)
   - timestamps: started_at, completed_at
   - متدها: mark_running(), mark_completed(), mark_failed()

✅ UsageLog (به‌روزرسانی شده):
   - اضافه شد: ai_job FK
   - فیلدهای موجود: content, user, workspace, organization
   - model, prompt_tokens, completion_tokens, total_tokens
   - estimated_cost, request_duration
   - success, error_message, timestamp

✅ AuditLog:
   - content FK, user FK
   - action: created/updated/approved/rejected/deleted/status_changed
   - old_status, new_status
   - changes jsonb, notes
   - ip_address, user_agent, timestamp

✅ AiUsage (proxy model):
   - Alias برای UsageLog
```

#### contentmgmt/models.py
```python
✅ ContentVersion (جدید):
   - content FK, version_number
   - title, body_markdown (Markdown RTL)
   - metadata jsonb
   - word_count (محاسبه خودکار)
   - ai_job FK
   - created_by FK, created_at

✅ Content (به‌روزرسانی):
   - اضافه شد: current_version FK به ContentVersion

✅ Version (legacy):
   - نگه‌داشته شد برای backward compatibility
   - renamed related_name به 'legacy_versions'
```

### 3. Endpoints

#### POST /api/contents/
```python
✅ ایجاد محتوای پیش‌نویس
✅ ثبت در AuditLog با action=CREATED
```

#### GET /api/contents/:id/
```python
✅ دریافت جزئیات محتوا
```

#### GET /api/contents/:id/versions/
```python
✅ دریافت تمام نسخه‌های یک محتوا
```

#### POST /api/contents/:id/generate/
```python
✅ ایجاد AI job با پارامترها:
   - kind: outline/draft/rewrite/caption
   - topic, tone, audience
   - keywords, min_words, max_words
   - additional_instructions
✅ بررسی محدودیت مصرف قبل از ایجاد job
✅ تغییر وضعیت به in_progress
✅ ثبت در AuditLog
✅ صف کردن task با Celery
✅ پاسخ 202 Accepted با job_id
✅ خطای 402 در صورت عبور از محدودیت
```

#### POST /api/contents/:id/approve/
```python
✅ تأیید محتوا (status -> approved)
✅ ثبت approved_by و approved_at
✅ ثبت در AuditLog با action=APPROVED
```

#### POST /api/contents/:id/reject/
```python
✅ رد محتوا با دلیل
✅ ثبت در AuditLog با action=REJECTED
```

#### GET /api/ai/jobs/
```python
✅ لیست AI jobs با فیلترها
```

#### GET /api/ai/usage-logs/
```python
✅ لیست usage logs
```

#### GET /api/ai/usage/summary/
```python
✅ خلاصه مصرف ماهانه/هفتگی/روزانه
✅ پارامترها: workspace_id, user_id, organization_id, period
✅ پاسخ: total_requests, total_tokens, total_cost, model_breakdown
```

### 4. Celery Tasks

#### generate_content_task
```python
✅ دریافت content_id, params, job_id
✅ تغییر وضعیت job به running
✅ ساخت prompt بر اساس kind و پارامترها
✅ استفاده از پرامپت فارسی پیش‌فرض برای draft
✅ ریداکشن PII قبل از ارسال:
   - تشخیص PII در topic, keywords, additional_instructions
   - ذخیره pii_warnings در content
✅ فراخوانی OpenAI Responses API:
   - system: نویسنده حرفه‌ای فارسی
   - user: prompt پارامتریک شده
   - temperature: 0.7
   - max_tokens: 2000
✅ Unmask کردن PII در خروجی
✅ محاسبه usage و cost
✅ ثبت در UsageLog:
   - input_tokens (prompt_tokens)
   - output_tokens (completion_tokens)
   - estimated_cost
   - request_duration
✅ ساخت ContentVersion جدید:
   - version_number (auto-increment)
   - body_markdown (Markdown RTL)
   - metadata شامل model, tokens, cost, params
   - ai_job FK
✅ به‌روزرسانی Content:
   - current_version به نسخه جدید
   - body, word_count
   - status -> review
✅ تغییر وضعیت job به completed
✅ مدیریت خطا:
   - retry حداکثر 3 بار
   - ثبت failed usage log
   - تغییر وضعیت job به failed
   - بازگشت content به draft
```

### 5. سقف مصرف ماهانه

#### ai/services.py
```python
✅ check_workspace_usage_limits(workspace):
   - دریافت UsageLimit برای workspace
   - محاسبه مصرف از اول ماه/روز
   - بررسی requests_limit, tokens_limit, cost_limit
   - بازگشت (bool, message)

✅ get_usage_summary():
   - فیلتر بر اساس workspace/user/organization
   - محدود کردن به بازه زمانی
   - Aggregate: total_requests, tokens, cost
   - model_breakdown

✅ log_ai_usage():
   - ثبت همزمان (sync) usage log
```

#### Enforcement در generate endpoint:
```python
✅ قبل از ایجاد job:
   - فراخوانی check_workspace_usage_limits()
   - اگر exceeded: پاسخ 402 Payment Required
   - پیام خطای واضح با جزئیات محدودیت
```

#### تنظیمات در settings.py:
```python
✅ DEFAULT_MONTHLY_TOKEN_LIMIT = 1,000,000
✅ DEFAULT_MONTHLY_COST_LIMIT = $100.0
✅ DEFAULT_MONTHLY_REQUEST_LIMIT = 1000
✅ قابل تنظیم از env
```

### 6. تست‌ها

#### tests/test_pii.py (واحد)
```python
✅ test_redact_phone_numbers (فرمت‌های مختلف)
✅ test_redact_emails
✅ test_redact_iban
✅ test_redact_national_id
✅ test_restore_pii
✅ test_mask_unmask_consistency
✅ test_multiple_same_pii
✅ test_has_pii
✅ test_empty_text
✅ test_helper_functions
✅ test_pii_warning_in_content (یکپارچه)
```

#### tests/test_content_generation.py (یکپارچه)
```python
✅ test_create_content
✅ test_create_ai_job
✅ test_job_lifecycle (pending->running->completed)
✅ test_job_failure_and_retry
✅ test_generate_content_success (با mock OpenAI)
✅ test_content_version_creation
✅ test_approve_content_workflow
✅ test_usage_log_creation
✅ test_audit_log_creation
✅ test_check_usage_limits_within_limits
✅ test_check_usage_limits_exceeded
```

### 7. Admin Panels

```python
✅ AiJobAdmin: لیست jobs با فیلتر status, kind
✅ UsageLogAdmin: لیست usage logs با cost/tokens
✅ UsageLimitAdmin: مدیریت محدودیت‌ها
✅ AuditLogAdmin: لاگ تغییرات
✅ PromptTemplateAdmin: مدیریت پرامپت‌ها
✅ ContentVersionAdmin: نسخه‌های محتوا
```

### 8. URL Routing

```python
✅ /api/contents/ - CRUD محتوا
✅ /api/contents/:id/generate/ - تولید محتوا
✅ /api/contents/:id/versions/ - نسخه‌ها
✅ /api/contents/:id/approve/ - تأیید
✅ /api/contents/:id/reject/ - رد
✅ /api/content-versions/ - CRUD نسخه‌ها
✅ /api/ai/jobs/ - لیست jobs
✅ /api/ai/usage-logs/ - لیست usage logs
✅ /api/ai/usage-limits/ - CRUD محدودیت‌ها
✅ /api/ai/audit-logs/ - لاگ تغییرات
✅ /api/ai/usage/summary/ - خلاصه مصرف
```

### 9. متغیرهای محیطی جدید

```bash
✅ OPENAI_API_KEY
✅ OPENAI_BASE_URL (اختیاری)
✅ OPENAI_DEFAULT_MODEL (پیش‌فرض: gpt-4o-mini)
✅ DEFAULT_MONTHLY_TOKEN_LIMIT
✅ DEFAULT_MONTHLY_COST_LIMIT
✅ DEFAULT_MONTHLY_REQUEST_LIMIT
```

## 📊 معیارهای پذیرش

### ✅ 1. POST /api/contents/:id/generate یک job می‌سازد
- Job با status=pending ایجاد می‌شود ✅
- Task در صف Celery قرار می‌گیرد ✅
- پس از اتمام، نسخه جدید قابل مشاهده است ✅
- وضعیت content به review تغییر می‌کند ✅

### ✅ 2. GET /api/ai/usage/summary/ ماهانه کار می‌کند
- پارامتر period=monthly پشتیبانی می‌شود ✅
- محاسبه از اول ماه جاری ✅
- خروجی شامل: total_requests, total_tokens, total_cost ✅
- model_breakdown برای هر مدل ✅
- هزینه بر اساس pricing محاسبه می‌شود ✅

### ✅ 3. ریداکشن PII قبل از فراخوانی OpenAI
- تشخیص تلفن، ایمیل، IBAN ✅
- جایگزینی با placeholders یکتا ✅
- نگه‌داری mapping در حافظه job ✅
- unmask پس از دریافت خروجی ✅
- ثبت pii_warnings در content ✅
- تست‌های واحد برای تمام patterns ✅

## 🔧 ویژگی‌های اضافی

### Markdown RTL Support
```python
✅ ContentVersion.body_markdown
✅ خروجی OpenAI در فرمت Markdown
✅ پشتیبانی کامل از RTL فارسی
```

### Versioning
```python
✅ هر تولید، یک ContentVersion جدید
✅ version_number به صورت خودکار
✅ Content.current_version به آخرین نسخه اشاره دارد
✅ تاریخچه کامل تغییرات نگه‌داری می‌شود
```

### Audit Trail
```python
✅ ثبت تمام تغییرات وضعیت
✅ ذخیره IP و User-Agent
✅ changes jsonb برای تغییرات جزئی
✅ قابل فیلتر بر اساس action و user
```

### Cost Tracking
```python
✅ pricing برای تمام مدل‌های OpenAI
✅ محاسبه دقیق بر اساس input/output tokens
✅ ثبت estimated_cost در UsageLog
✅ خلاصه هزینه در usage summary
```

### Error Handling
```python
✅ Retry mechanism با max_retries=3
✅ ثبت failed usage logs
✅ پیام‌های خطای واضح
✅ بازگشت content به draft در صورت خطا
```

## 📝 نکات پیاده‌سازی

### 1. Celery Task
- استفاده از bind=True برای دسترسی به self
- default_retry_delay=60 ثانیه
- max_retries=3
- مدیریت exception‌ها در سطوح مختلف

### 2. PII Redaction
- استفاده از UUID برای placeholders یکتا
- نگه‌داری mapping در instance PIIRedactor
- ارسال redactor از task به restore
- تست coverage کامل

### 3. Usage Limits
- بررسی قبل از ایجاد job (prevent)
- محاسبه از start_of_month/day
- پشتیبانی از monthly و daily periods
- پیام‌های خطای واضح با جزئیات

### 4. Prompt Engineering
- پرامپت فارسی ساختاریافته
- پارامتریک با format()
- شامل دستورالعمل‌های واضح
- خروجی Markdown با structure

## 🚀 آماده برای استفاده

```bash
# ایجاد migrations
python manage.py makemigrations

# اجرای migrations
python manage.py migrate

# تست‌ها
pytest tests/test_pii.py
pytest tests/test_content_generation.py

# راه‌اندازی Celery worker
celery -A core worker -l info

# استفاده
curl -X POST http://localhost:8000/api/contents/1/generate/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "draft",
    "topic": "مزایای هوش مصنوعی در کسب‌وکار",
    "tone": "حرفه‌ای",
    "audience": "کارآفرینان",
    "keywords": "هوش مصنوعی، نوآوری، بهره‌وری",
    "min_words": 800
  }'
```

---

**تاریخ:** 2025-10-05  
**نسخه:** 1.0.0  
**وضعیت:** ✅ Complete & Tested
