# معماری سیستم Contexor

## نگاه کلی (Overview)

Contexor یک پلتفرم تولید محتوای هوشمند است که به سازمان‌ها امکان می‌دهد با استفاده از مدل‌های زبانی OpenAI، محتوای متنی تولید، مدیریت و تأیید کنند. سیستم شامل احراز هویت OTP، مدیریت سازمان/فضای کاری، تولید محتوا با جریان تأیید، و پیگیری مصرف API است.

## استک فناوری (Technology Stack)

### نسخه‌های مورد نیاز

| Component | Version | Description |
|-----------|---------|-------------|
| **Backend** | | |
| Django | 5.0.x | Web framework اصلی |
| Django REST Framework | 3.16.x | REST API framework |
| djangorestframework-simplejwt | 5.3.x | JWT authentication |
| PostgreSQL | 15 | Database اصلی |
| Redis | 7 | Cache و message broker |
| Celery | 5.3.x | Task queue برای عملیات async |
| **Frontend** | | |
| Next.js | 15.0 | React framework با App Router |
| React | 18.3.x | UI library |
| TypeScript | 5.x | Type-safe JavaScript |
| **External Services** | | |
| OpenAI API | Latest | تولید محتوا (مدل پیش‌فرض: gpt-4.1-mini) |
| Kavenegar | Latest | ارسال SMS برای OTP |
| **Infrastructure** | | |
| Docker | Latest | Containerization |
| Docker Compose | Latest | Multi-container orchestration |

## معماری کلی (High-Level Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CLIENT (Browser)                                 │
│                      Next.js 15 App Router Frontend                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTP/REST
                                 │ Bearer Token Auth
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (Django/DRF)                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   Auth API       │  │   Content API    │  │   Usage API      │          │
│  │   (OTP/JWT)      │  │   (CRUD/Generate)│  │   (Tracking)     │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                      │                    │
│           └─────────────────────┼──────────────────────┘                    │
│                                 │                                           │
│  ┌──────────────────────────────┴───────────────────────────────────────┐  │
│  │                      Django ORM / Models                              │  │
│  │   User, Organization, Workspace, Project, Content, Version,           │  │
│  │   Prompt, UsageLog, UsageLimit                                        │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
└─────────────────────────────────┼────────────────────────────────────────────┘
                                  │
                                  ↓
                ┌─────────────────────────────────────┐
                │      PostgreSQL 15 Database         │
                │  - Users & Organizations            │
                │  - Content & Versions               │
                │  - Usage Logs & Limits              │
                └─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         ASYNC WORKERS (Celery)                               │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │  Celery Worker                                                    │      │
│  │   - generate_content_task()                                       │      │
│  │   - detect_pii_task()                                             │      │
│  │   - log_usage_task()                                              │      │
│  │   - send_otp_sms_task()                                           │      │
│  └────────────────────────┬─────────────────────────────────────────┘      │
│                           │                                                 │
│  ┌────────────────────────┴─────────────────────────────────────────┐      │
│  │  Celery Beat (Scheduler)                                          │      │
│  │   - monthly_usage_reset                                           │      │
│  │   - cleanup_expired_otps                                          │      │
│  └───────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  ↓
                ┌─────────────────────────────────────┐
                │         Redis 7                     │
                │  - Celery Broker                    │
                │  - Celery Results                   │
                │  - Session Cache                    │
                │  - OTP Storage (TTL)                │
                └─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                      │
│  ┌──────────────────────┐        ┌──────────────────────┐                  │
│  │   OpenAI API         │        │   Kavenegar SMS      │                  │
│  │   - GPT-4.1-mini     │        │   - OTP Delivery     │                  │
│  │   - Content Gen      │        │                      │                  │
│  │   - PII Detection    │        │                      │                  │
│  └──────────────────────┘        └──────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## لایه‌های معماری (Architecture Layers)

### 1. Frontend Layer (Next.js 15)

```
frontend/
  app/                    # App Router pages
    (auth)/
      login/             # صفحه ورود با OTP
    (dashboard)/
      projects/          # لیست پروژه‌ها
      contents/          # لیست محتواها
      editor/            # ویرایشگر محتوا
      usage/             # داشبورد مصرف
  components/            # React components
    ui/                  # کامپوننت‌های عمومی UI
    forms/               # فرم‌های اپلیکیشن
    content/             # کامپوننت‌های مرتبط با محتوا
  lib/
    api.ts               # API client (axios)
    auth.ts              # Auth utilities
    store.ts             # Zustand state management
```

**ویژگی‌ها:**
- Server Components برای SEO و Performance
- Client Components برای تعاملات
- Middleware برای Auth Guard
- API Routes برای proxy (در صورت نیاز)

### 2. Backend Layer (Django/DRF)

```
backend/
  core/                  # تنظیمات اصلی Django
    settings.py          # Configuration
    celery.py            # Celery config
    urls.py              # Root URL routing
  
  accounts/              # مدیریت کاربران و احراز هویت
    models.py            # User, Organization, Workspace
    views.py             # OTP request/verify APIs
    serializers.py       # DRF serializers
    permissions.py       # Custom permissions
  
  contentmgmt/           # مدیریت محتوا
    models.py            # Project, Content, Version, Prompt
    views.py             # CRUD APIs
    serializers.py       # DRF serializers
    services.py          # Business logic
  
  ai/                    # سرویس‌های AI
    service.py           # OpenAI integration
    tasks.py             # Celery tasks
    models.py            # UsageLog, UsageLimit
    pii.py               # PII detection
```

### 3. Data Layer (PostgreSQL)

مدل‌های اصلی:
- **User**: کاربران سیستم
- **Organization**: سازمان‌ها
- **Workspace**: فضاهای کاری در سازمان
- **Project**: پروژه‌های محتوایی
- **Content**: محتواهای تولید شده
- **Version**: نسخه‌های محتوا
- **Prompt**: پرامپت‌های قابل استفاده مجدد
- **UsageLog**: لاگ مصرف API
- **UsageLimit**: محدودیت مصرف

### 4. Task Queue Layer (Celery + Redis)

**Tasks:**
- `generate_content_task()`: تولید محتوا از OpenAI
- `detect_pii_task()`: تشخیص اطلاعات حساس
- `log_usage_task()`: ثبت مصرف API
- `send_otp_sms_task()`: ارسال SMS

**Periodic Tasks (Celery Beat):**
- `monthly_usage_reset`: ریست مصرف ماهانه
- `cleanup_expired_otps`: پاکسازی OTPهای منقضی

## جریان‌های اصلی (Main Flows)

### 1. جریان احراز هویت OTP

```
User                    Frontend              Backend              Kavenegar
  │                        │                      │                     │
  │ Enter Phone Number     │                      │                     │
  ├───────────────────────>│                      │                     │
  │                        │ POST /auth/otp/request                   │
  │                        ├─────────────────────>│                     │
  │                        │                      │ Send SMS            │
  │                        │                      ├────────────────────>│
  │                        │                      │                     │
  │                        │ { ttl: 120 }         │                     │
  │                        │<─────────────────────┤                     │
  │ Show OTP Input         │                      │                     │
  │<───────────────────────┤                      │                     │
  │                        │                      │                     │
  │ Enter OTP Code         │                      │                     │
  ├───────────────────────>│                      │                     │
  │                        │ POST /auth/otp/verify                     │
  │                        ├─────────────────────>│                     │
  │                        │                      │ Validate OTP        │
  │                        │                      │ Generate JWT        │
  │                        │ { access, refresh }  │                     │
  │                        │<─────────────────────┤                     │
  │ Store Token            │                      │                     │
  │ Redirect to Dashboard  │                      │                     │
  │<───────────────────────┤                      │                     │
```

### 2. جریان تولید محتوا

```
State Flow: DRAFT → IN_PROGRESS → REVIEW → APPROVED/REJECTED

User          Frontend        Backend        Celery Worker      OpenAI
  │              │               │                 │               │
  │ Create New   │               │                 │               │
  │ Content      │               │                 │               │
  ├─────────────>│               │                 │               │
  │              │ POST /contents│                 │               │
  │              ├──────────────>│                 │               │
  │              │               │ Create (DRAFT)  │               │
  │              │               │ status          │               │
  │              │ { id, status }│                 │               │
  │              │<──────────────┤                 │               │
  │              │               │                 │               │
  │ Request      │               │                 │               │
  │ Generate     │               │                 │               │
  ├─────────────>│               │                 │               │
  │              │ POST /contents/:id/generate     │               │
  │              ├──────────────>│                 │               │
  │              │               │ Update status   │               │
  │              │               │ to IN_PROGRESS  │               │
  │              │               │ Queue task      │               │
  │              │               ├────────────────>│               │
  │              │ { task_id }   │                 │ Call API      │
  │              │<──────────────┤                 ├──────────────>│
  │              │               │                 │               │
  │ Poll Status  │               │                 │ Response      │
  │ (or WebSocket)              │                 │<──────────────┤
  ├─────────────>│               │                 │               │
  │              │ GET /contents/:id               │ Log Usage     │
  │              ├──────────────>│                 │ Update Content│
  │              │ { status:     │                 │ to REVIEW     │
  │              │   REVIEW }    │<────────────────┤               │
  │              │<──────────────┤                 │               │
  │              │               │                 │               │
  │ Review       │               │                 │               │
  │ & Approve    │               │                 │               │
  ├─────────────>│               │                 │               │
  │              │ POST /contents/:id/approve      │               │
  │              ├──────────────>│                 │               │
  │              │               │ Update to       │               │
  │              │               │ APPROVED        │               │
  │              │ Success       │ Create Version  │               │
  │              │<──────────────┤                 │               │
```

### 3. جریان ثبت Usage و بررسی سقف

```
Task (after OpenAI call)   UsageLog Model      UsageLimit Model
         │                      │                     │
         │ Log usage            │                     │
         ├─────────────────────>│                     │
         │ (tokens, cost, etc.) │                     │
         │                      │ Get current month   │
         │                      │ usage for user/org  │
         │                      │────────────────────>│
         │                      │                     │
         │                      │ Check if exceeds    │
         │                      │<────────────────────┤
         │                      │                     │
         │ If exceeded:         │                     │
         │ - Raise exception    │                     │
         │ - Notify user        │                     │
         │                      │                     │
```

## الزامات MoSCoW

### Must Have (باید داشته باشد)

1. **احراز هویت:**
   - ورود با شماره تلفن و OTP
   - JWT برای authentication
   - مدیریت access/refresh tokens

2. **مدیریت سازمان:**
   - سازمان چندکاربره
   - فضاهای کاری (Workspaces)
   - سطوح دسترسی (Admin, Editor, Viewer)

3. **تولید محتوا:**
   - ساخت محتوا با پرامپت
   - تولید متن از OpenAI
   - جریان تأیید (Draft → Review → Approved)
   - ذخیره نسخه‌ها

4. **پیگیری مصرف:**
   - ثبت تعداد توکن و هزینه
   - محدودیت مصرف ماهانه
   - داشبورد مصرف

5. **پرامپت‌های قابل استفاده مجدد:**
   - ذخیره و مدیریت پرامپت‌ها
   - دسته‌بندی پرامپت‌ها

### Should Have (باید داشته باشد)

1. تشخیص PII در محتوای تولید شده
2. فیلتر و جستجوی پیشرفته محتوا
3. Export محتوا (JSON, Markdown)
4. Webhook برای notify در تکمیل generation

### Could Have (می‌تواند داشته باشد)

1. پیش‌نمایش زنده محتوا
2. مقایسه نسخه‌های مختلف
3. Template system برای پرامپت‌ها
4. Analytics پیشرفته

### Won't Have (در نسخه اول نیست)

1. Multi-language UI
2. Fine-tuning مدل‌های OpenAI
3. Integration با CMS خارجی
4. Mobile app

## امنیت (Security)

1. **Authentication:**
   - JWT با expiry کوتاه (60min)
   - Refresh token برای تمدید
   - OTP با TTL 2 دقیقه

2. **Authorization:**
   - Permission-based access control
   - Organization/Workspace isolation
   - Role-based permissions

3. **Data Protection:**
   - تشخیص PII قبل از ذخیره
   - هشدار به کاربر در صورت وجود اطلاعات حساس
   - Encryption برای دیتای حساس

4. **API Security:**
   - Rate limiting
   - CORS configuration
   - Input validation و sanitization

## مقیاس‌پذیری (Scalability)

1. **Horizontal Scaling:**
   - Django instances پشت load balancer
   - Multiple Celery workers
   - Redis cluster

2. **Database:**
   - Read replicas
   - Connection pooling
   - Proper indexing

3. **Caching:**
   - Redis برای session و cache
   - Query result caching

4. **Async Processing:**
   - تمام عملیات سنگین در Celery
   - Rate limiting برای OpenAI calls

## مانیتورینگ و Logging

1. **Application Logs:**
   - Django logging
   - Celery task logs
   - Error tracking

2. **Metrics:**
   - API response times
   - Task queue length
   - Database query performance
   - OpenAI API usage

3. **Alerts:**
   - Failed tasks
   - High error rates
   - Usage limit warnings

## ملاحظات استقرار (Deployment)

1. **Development:**
   - Docker Compose برای local dev
   - Hot reload برای frontend و backend

2. **Production:**
   - Docker containers
   - Environment-based configuration
   - Secret management
   - Database backups
   - Log aggregation

## مراجع و منابع

- Django Documentation: https://docs.djangoproject.com/
- DRF Documentation: https://www.django-rest-framework.org/
- Next.js Documentation: https://nextjs.org/docs
- OpenAI API Reference: https://platform.openai.com/docs/api-reference
- Celery Documentation: https://docs.celeryproject.org/
- Kavenegar API: https://kavenegar.com/rest.html
