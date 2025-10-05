# راهنمای استفاده از سیستم تولید محتوای هوشمند

این راهنما نحوه استفاده از API های تولید محتوای هوشمند با OpenAI، ریداکشن PII، و مدیریت مصرف را توضیح می‌دهد.

## 📋 فهرست

1. [راه‌اندازی اولیه](#راه-اندازی-اولیه)
2. [ایجاد محتوا](#ایجاد-محتوا)
3. [تولید محتوا با AI](#تولید-محتوا-با-ai)
4. [مشاهده نسخه‌ها](#مشاهده-نسخه-ها)
5. [تأیید و رد محتوا](#تأیید-و-رد-محتوا)
6. [مدیریت محدودیت‌های مصرف](#مدیریت-محدودیت-های-مصرف)
7. [نظارت بر مصرف](#نظارت-بر-مصرف)

## راه‌اندازی اولیه

### 1. تنظیم متغیرهای محیطی

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-4o-mini

# Usage Limits (اختیاری)
DEFAULT_MONTHLY_TOKEN_LIMIT=1000000
DEFAULT_MONTHLY_COST_LIMIT=100.0
DEFAULT_MONTHLY_REQUEST_LIMIT=1000
```

### 2. اجرای Migrations

```bash
python manage.py migrate
```

### 3. راه‌اندازی Celery Worker

```bash
# Terminal 1: Celery Worker
celery -A core worker -l info

# Terminal 2: Celery Beat (برای وظایف زمان‌بندی شده)
celery -A core beat -l info
```

## ایجاد محتوا

### ایجاد پروژه

```bash
POST /api/projects/
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "name": "وبلاگ شرکت",
  "slug": "company-blog",
  "workspace": 1,
  "description": "مقالات وبلاگ شرکت"
}
```

### ایجاد محتوای پیش‌نویس

```bash
POST /api/contents/
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "title": "مزایای هوش مصنوعی در کسب‌وکار",
  "project": 1,
  "status": "draft"
}
```

**پاسخ:**
```json
{
  "id": 123,
  "title": "مزایای هوش مصنوعی در کسب‌وکار",
  "status": "draft",
  "project": 1,
  "word_count": 0,
  "has_pii": false,
  "created_at": "2025-10-05T10:00:00Z"
}
```

## تولید محتوا با AI

### درخواست تولید محتوا

```bash
POST /api/contents/123/generate/
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "kind": "draft",
  "topic": "مزایای هوش مصنوعی در کسب‌وکار",
  "tone": "حرفه‌ای",
  "audience": "کارآفرینان و مدیران",
  "keywords": "هوش مصنوعی، نوآوری، بهره‌وری، اتوماسیون",
  "min_words": 800,
  "additional_instructions": "تمرکز بر مثال‌های عملی و کاربردی"
}
```

**پارامترها:**

- `kind` (الزامی): نوع تولید
  - `outline`: ساختار و خلاصه
  - `draft`: پیش‌نویس کامل
  - `rewrite`: بازنویسی محتوای موجود
  - `caption`: کپشن کوتاه (برای شبکه‌های اجتماعی)

- `topic` (اختیاری): موضوع محتوا
- `tone` (اختیاری، پیش‌فرض: "حرفه‌ای"): لحن نوشتار
  - حرفه‌ای، دوستانه، رسمی، صمیمی، آموزشی، ...
  
- `audience` (اختیاری، پیش‌فرض: "عمومی"): مخاطب هدف
- `keywords` (اختیاری): کلمات کلیدی (با ویرگول جدا شده)
- `min_words` (اختیاری، پیش‌فرض: 500): حداقل تعداد کلمات
- `max_words` (اختیاری): حداکثر تعداد کلمات
- `additional_instructions` (اختیاری): دستورالعمل‌های اضافی

**پاسخ (202 Accepted):**
```json
{
  "job_id": 456,
  "status": "pending",
  "message": "Content generation started",
  "content": {
    "id": 123,
    "status": "in_progress",
    ...
  }
}
```

### بررسی وضعیت Job

```bash
GET /api/ai/jobs/456/
Authorization: Bearer YOUR_TOKEN
```

**پاسخ:**
```json
{
  "id": 456,
  "content": 123,
  "status": "completed",
  "kind": "draft",
  "result_data": {
    "version_id": 789,
    "version_number": 1,
    "tokens": 1250,
    "cost": 0.00025
  },
  "started_at": "2025-10-05T10:01:00Z",
  "completed_at": "2025-10-05T10:01:15Z"
}
```

**وضعیت‌های ممکن:**
- `pending`: در صف
- `running`: در حال اجرا
- `completed`: تکمیل شده
- `failed`: خطا
- `cancelled`: لغو شده

### خطاها

#### محدودیت مصرف
```json
HTTP 402 Payment Required

{
  "error": "Usage limit exceeded",
  "detail": "Token limit exceeded: 1250000/1000000"
}
```

## مشاهده نسخه‌ها

### دریافت تمام نسخه‌های یک محتوا

```bash
GET /api/contents/123/versions/
Authorization: Bearer YOUR_TOKEN
```

**پاسخ:**
```json
[
  {
    "id": 789,
    "version_number": 2,
    "title": "مزایای هوش مصنوعی در کسب‌وکار",
    "body_markdown": "# عنوان\n\nمحتوای مارک‌داون...",
    "word_count": 850,
    "metadata": {
      "kind": "draft",
      "model": "gpt-4o-mini",
      "tokens": 1250,
      "cost": 0.00025
    },
    "ai_job": 456,
    "created_at": "2025-10-05T10:01:15Z"
  },
  {
    "id": 788,
    "version_number": 1,
    ...
  }
]
```

### دریافت یک نسخه خاص

```bash
GET /api/content-versions/789/
Authorization: Bearer YOUR_TOKEN
```

## تأیید و رد محتوا

### تأیید محتوا

```bash
POST /api/contents/123/approve/
Authorization: Bearer YOUR_TOKEN
```

**شرایط:**
- محتوا باید در وضعیت `review` باشد

**پاسخ:**
```json
{
  "id": 123,
  "status": "approved",
  "approved_by": 1,
  "approved_at": "2025-10-05T11:00:00Z",
  ...
}
```

### رد محتوا

```bash
POST /api/contents/123/reject/
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "reason": "نیاز به ویرایش بیشتر دارد"
}
```

**پاسخ:**
```json
{
  "id": 123,
  "status": "rejected",
  "rejection_reason": "نیاز به ویرایش بیشتر دارد",
  ...
}
```

## مدیریت محدودیت‌های مصرف

### ایجاد محدودیت برای Workspace

```bash
POST /api/ai/usage-limits/
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "scope": "workspace",
  "scope_id": 1,
  "tokens_limit": 1000000,
  "cost_limit": 100.0,
  "requests_limit": 1000,
  "period": "monthly"
}
```

**پارامترها:**
- `scope`: سطح محدودیت
  - `user`: کاربر
  - `workspace`: فضای کاری
  - `organization`: سازمان
  
- `scope_id`: شناسه موجودیت (user_id, workspace_id, organization_id)
- `tokens_limit`: حداکثر تعداد توکن
- `cost_limit`: حداکثر هزینه (دلار)
- `requests_limit`: حداکثر تعداد درخواست
- `period`: دوره
  - `monthly`: ماهانه (از اول ماه)
  - `daily`: روزانه (از 00:00)

### به‌روزرسانی محدودیت

```bash
PATCH /api/ai/usage-limits/1/
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "tokens_limit": 2000000,
  "cost_limit": 200.0
}
```

### حذف محدودیت

```bash
DELETE /api/ai/usage-limits/1/
Authorization: Bearer YOUR_TOKEN
```

## نظارت بر مصرف

### خلاصه مصرف ماهانه

```bash
GET /api/ai/usage/summary/?workspace_id=1&period=monthly
Authorization: Bearer YOUR_TOKEN
```

**پاسخ:**
```json
{
  "period": "monthly",
  "start_date": "2025-10-01T00:00:00Z",
  "end_date": "2025-10-05T12:00:00Z",
  "summary": {
    "total_requests": 15,
    "total_prompt_tokens": 5000,
    "total_completion_tokens": 12000,
    "total_tokens": 17000,
    "total_cost": 0.0034,
    "model_breakdown": {
      "gpt-4o-mini": {
        "requests": 10,
        "tokens": 12000,
        "cost": 0.0024
      },
      "gpt-4o": {
        "requests": 5,
        "tokens": 5000,
        "cost": 0.001
      }
    }
  }
}
```

**پارامترها:**
- `workspace_id` (اختیاری): فیلتر بر اساس workspace
- `user_id` (اختیاری): فیلتر بر اساس کاربر
- `organization_id` (اختیاری): فیلتر بر اساس سازمان
- `period` (اختیاری، پیش‌فرض: "monthly"):
  - `monthly`: ماه جاری
  - `weekly`: هفته گذشته
  - `daily`: امروز
  - `all`: همه زمان‌ها

### لیست Usage Logs

```bash
GET /api/ai/usage-logs/?workspace=1&model=gpt-4o-mini
Authorization: Bearer YOUR_TOKEN
```

**فیلترها:**
- `workspace`: فضای کاری
- `user`: کاربر
- `organization`: سازمان
- `model`: مدل OpenAI
- `success`: موفق/ناموفق (true/false)

### لیست Audit Logs

```bash
GET /api/ai/audit-logs/?content=123
Authorization: Bearer YOUR_TOKEN
```

**فیلترها:**
- `content`: محتوا
- `user`: کاربر
- `action`: نوع عملیات
  - `created`
  - `updated`
  - `approved`
  - `rejected`
  - `status_changed`

## ریداکشن PII

سیستم به صورت خودکار اطلاعات شخصی (PII) را قبل از ارسال به OpenAI شناسایی و ریداکت می‌کند:

### الگوهای شناسایی شده:
- **شماره تلفن ایران:** `09123456789`, `+989123456789`, `9123456789`
- **ایمیل:** `user@example.com`
- **IBAN ایران:** `IR123456789012345678901234`

### مثال:

**ورودی (با PII):**
```json
{
  "topic": "تماس با 09123456789 یا ایمیل info@company.ir"
}
```

**ارسال به OpenAI (ریداکت شده):**
```
تماس با [PHONE_a1b2c3d4] یا ایمیل [EMAIL_e5f6g7h8]
```

**خروجی (بازیابی شده):**
```
تماس با 09123456789 یا ایمیل info@company.ir
```

**هشدار PII در Content:**
```json
{
  "has_pii": true,
  "pii_warnings": {
    "phone": ["Found 1 phone number(s)"],
    "email": ["Found 1 email address(es)"]
  }
}
```

## نکات مهم

### ⚠️ امنیت
- همیشه از HTTPS استفاده کنید
- API keys را secure نگه دارید
- محدودیت‌های مصرف را تنظیم کنید

### 💡 بهینه‌سازی
- از `gpt-4o-mini` برای صرفه‌جویی در هزینه استفاده کنید
- `min_words` را متناسب با نیاز تنظیم کنید
- از cache برای نتایج تکراری استفاده کنید

### 🔧 عیب‌یابی

**Job در وضعیت Failed:**
```bash
GET /api/ai/jobs/456/
```
بررسی کنید:
- `error_message`: پیام خطا
- `retry_count`: تعداد تلاش‌های مجدد
- Usage logs برای جزئیات بیشتر

**OpenAI API Error:**
- API key را بررسی کنید
- اتصال اینترنت را چک کنید
- محدودیت rate limit OpenAI را بررسی کنید

## پشتیبانی

برای سوالات و مشکلات:
- مستندات کامل: `/api/docs/`
- Admin panel: `/admin/`
- Logs: فایل‌های log Django و Celery

---

**نسخه:** 1.0.0  
**تاریخ:** 2025-10-05
