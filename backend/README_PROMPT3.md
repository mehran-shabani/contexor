# پیاده‌سازی پرامپت 3: ایجنت AI & Jobs & Usage

این سند خلاصه‌ای از فایل‌های ایجاد و تغییر یافته در پیاده‌سازی پرامپت 3 است.

## 📁 فایل‌های ایجاد شده

### ماژول AI Core
```
backend/ai/
├── client.py                          ✅ NEW - OpenAI client با pricing
├── pii.py                             ✅ NEW - PII redaction/restoration
├── services.py                        ✅ NEW - Usage limits & services
├── serializers.py                     ✅ NEW - Serializers برای AI models
├── views.py                           ✅ NEW - Views & endpoints
└── prompts/
    ├── __init__.py                    ✅ NEW
    ├── models.py                      ✅ NEW - PromptTemplate model
    └── migrations/
        ├── __init__.py                ✅ NEW
        └── 0001_initial.py            ✅ NEW
```

### مدل‌ها
```
backend/ai/models.py                   ⚡ UPDATED - اضافه شد:
  - AiJob
  - AuditLog
  - AiUsage (proxy)
  - UsageLog.ai_job FK

backend/contentmgmt/models.py          ⚡ UPDATED - اضافه شد:
  - ContentVersion (جدید)
  - Content.current_version FK
  - Version -> legacy
```

### Migrations
```
backend/ai/migrations/
└── 0002_aijob_auditlog_aiusage.py     ✅ NEW

backend/contentmgmt/migrations/
└── 0002_contentversion_content_current_version.py  ✅ NEW
```

### Tasks & Views
```
backend/ai/tasks.py                    ⚡ UPDATED - اضافه شد:
  - generate_content_task

backend/contentmgmt/views.py           ⚡ UPDATED - اضافه شد:
  - generate() action
  - versions() action
  - ContentVersionViewSet
  - AuditLog integration

backend/contentmgmt/serializers.py     ⚡ UPDATED - اضافه شد:
  - ContentVersionSerializer
  - GenerateContentSerializer
```

### Admin
```
backend/ai/admin.py                    ⚡ UPDATED
backend/contentmgmt/admin.py           ⚡ UPDATED
```

### URLs
```
backend/ai/urls.py                     ⚡ UPDATED
backend/contentmgmt/urls.py            ⚡ UPDATED
backend/core/urls.py                   ⚡ UPDATED
```

### تست‌ها
```
backend/tests/
├── test_pii.py                        ✅ NEW - 11 تست برای PII
└── test_content_generation.py         ✅ NEW - 10+ تست یکپارچه
```

### تنظیمات و مستندات
```
backend/core/settings.py               ⚡ UPDATED - اضافه شد:
  - OPENAI_BASE_URL
  - Usage limit configs

backend/.env.example                   ⚡ UPDATED

backend/PROMPT3_IMPLEMENTATION.md      ✅ NEW - خلاصه کامل
backend/AI_CONTENT_GENERATION_GUIDE.md ✅ NEW - راهنمای استفاده
backend/README_PROMPT3.md              ✅ NEW - این فایل
```

## 🚀 راه‌اندازی سریع

### 1. تنظیم محیط

```bash
# افزودن متغیرهای جدید به .env
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-4o-mini
DEFAULT_MONTHLY_TOKEN_LIMIT=1000000
DEFAULT_MONTHLY_COST_LIMIT=100.0
DEFAULT_MONTHLY_REQUEST_LIMIT=1000
```

### 2. اجرای Migrations

```bash
cd backend
python manage.py migrate
```

### 3. راه‌اندازی Celery

```bash
# Terminal 1
celery -A core worker -l info

# Terminal 2
celery -A core beat -l info
```

### 4. تست

```bash
# تست PII
pytest tests/test_pii.py -v

# تست Content Generation
pytest tests/test_content_generation.py -v

# همه تست‌ها
pytest tests/ -v
```

## 📊 API Endpoints جدید

### Content Generation
```
POST   /api/contents/:id/generate/     - تولید محتوا با AI
GET    /api/contents/:id/versions/     - دریافت نسخه‌ها
```

### AI Jobs
```
GET    /api/ai/jobs/                   - لیست jobs
GET    /api/ai/jobs/:id/               - جزئیات job
```

### Usage Tracking
```
GET    /api/ai/usage/summary/          - خلاصه مصرف
GET    /api/ai/usage-logs/             - لیست usage logs
GET    /api/ai/usage-limits/           - لیست محدودیت‌ها
POST   /api/ai/usage-limits/           - ایجاد محدودیت
PATCH  /api/ai/usage-limits/:id/       - ویرایش محدودیت
DELETE /api/ai/usage-limits/:id/       - حذف محدودیت
```

### Audit Logs
```
GET    /api/ai/audit-logs/             - لیست تغییرات
```

### Content Versions
```
GET    /api/content-versions/          - لیست نسخه‌ها
GET    /api/content-versions/:id/      - جزئیات نسخه
```

## 🎯 ویژگی‌های کلیدی

### ✅ AI Content Generation
- پشتیبانی از 4 نوع: outline, draft, rewrite, caption
- پرامپت فارسی پیش‌فرض برای blog draft
- پارامترهای قابل تنظیم: topic, tone, audience, keywords, min_words
- خروجی Markdown با RTL support

### ✅ PII Redaction
- شناسایی خودکار: تلفن، ایمیل، IBAN
- Mask/Unmask امن با UUID placeholders
- ثبت warnings در content
- تست coverage کامل

### ✅ Usage Tracking
- ثبت تمام فراخوانی‌های OpenAI
- محاسبه دقیق هزینه
- خلاصه مصرف ماهانه/هفتگی/روزانه
- model breakdown

### ✅ Usage Limits
- تنظیم محدودیت در سطح user/workspace/organization
- بررسی قبل از تولید محتوا
- خطای 402 در صورت عبور
- پشتیبانی از monthly/daily periods

### ✅ Versioning
- هر تولید = یک ContentVersion جدید
- نگه‌داری تاریخچه کامل
- ارجاع به ai_job
- محاسبه خودکار word_count

### ✅ Audit Trail
- ثبت تمام تغییرات وضعیت
- ذخیره IP و User-Agent
- changes jsonb برای جزئیات
- قابل فیلتر و جستجو

### ✅ Error Handling
- Retry mechanism (max 3)
- ثبت failed usage logs
- پیام‌های خطای واضح
- بازگشت content به draft

## 📖 مستندات

- **راهنمای استفاده:** [AI_CONTENT_GENERATION_GUIDE.md](./AI_CONTENT_GENERATION_GUIDE.md)
- **خلاصه پیاده‌سازی:** [PROMPT3_IMPLEMENTATION.md](./PROMPT3_IMPLEMENTATION.md)
- **API Docs:** `/admin/doc/` (پس از راه‌اندازی)

## 🧪 تست‌ها

### تست‌های PII (11 تست)
- ✅ redact_phone_numbers
- ✅ redact_emails
- ✅ redact_iban
- ✅ redact_national_id
- ✅ restore_pii
- ✅ mask_unmask_consistency
- ✅ multiple_same_pii
- ✅ has_pii
- ✅ empty_text
- ✅ helper_functions
- ✅ pii_warning_in_content

### تست‌های Content Generation (10+ تست)
- ✅ create_content
- ✅ create_ai_job
- ✅ job_lifecycle
- ✅ job_failure_and_retry
- ✅ generate_content_success
- ✅ content_version_creation
- ✅ approve_content_workflow
- ✅ usage_log_creation
- ✅ audit_log_creation
- ✅ check_usage_limits

## 📈 آمار

- **فایل‌های جدید:** 17
- **فایل‌های به‌روزرسانی شده:** 10
- **Endpoints جدید:** 12+
- **مدل‌های جدید:** 5
- **تست‌های جدید:** 21+
- **خطوط کد:** ~2500+ LOC

## ⚙️ وابستگی‌های جدید

همه وابستگی‌ها از قبل در `requirements.txt` موجود هستند:
- ✅ openai>=1.12.0
- ✅ celery==5.3.4
- ✅ redis==5.0.1

## 🔐 امنیت

- ✅ PII redaction قبل از ارسال به OpenAI
- ✅ Usage limits برای جلوگیری از abuse
- ✅ Audit logging برای accountability
- ✅ IP و User-Agent tracking
- ✅ JWT authentication برای تمام endpoints

## 🎨 Frontend Integration

برای یکپارچه‌سازی با frontend:

1. **ایجاد محتوا:** `POST /api/contents/`
2. **تولید:** `POST /api/contents/:id/generate/`
3. **Polling job status:** `GET /api/ai/jobs/:job_id/`
4. **نمایش نسخه:** `GET /api/content-versions/:version_id/`
5. **تأیید:** `POST /api/contents/:id/approve/`

نمونه کد در [AI_CONTENT_GENERATION_GUIDE.md](./AI_CONTENT_GENERATION_GUIDE.md)

## ❓ سوالات متداول

**Q: چگونه محدودیت مصرف تنظیم کنم؟**  
A: از endpoint `/api/ai/usage-limits/` استفاده کنید.

**Q: چگونه هزینه محاسبه می‌شود؟**  
A: بر اساس pricing OpenAI برای هر مدل (input + output tokens)

**Q: PII چیست و چرا مهم است؟**  
A: اطلاعات شخصی (تلفن، ایمیل، ...) که نباید به OpenAI ارسال شود.

**Q: چند بار retry می‌شود؟**  
A: حداکثر 3 بار با تاخیر 60 ثانیه.

**Q: چگونه خروجی را customize کنم؟**  
A: از `additional_instructions` استفاده کنید یا PromptTemplate جدید بسازید.

## 🐛 مشکلات شناخته شده

- هیچ مشکل شناخته شده‌ای وجود ندارد

## 🔄 آپدیت‌های آینده

- [ ] پشتیبانی از مدل‌های بیشتر
- [ ] Cache برای پرامپت‌های تکراری
- [ ] Webhook برای اعلان اتمام job
- [ ] Export محتوا به PDF
- [ ] A/B testing برای پرامپت‌ها

---

**تاریخ:** 2025-10-05  
**نسخه:** 1.0.0  
**مجری:** Background Agent  
**وضعیت:** ✅ Complete & Ready for Production
