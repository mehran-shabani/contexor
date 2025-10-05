# Contexor Backend - Django/DRF

این بک‌اند سیستم Contexor با استفاده از Django 5.0 و Django REST Framework پیاده‌سازی شده است.

## ویژگی‌های پیاده‌سازی شده

### 1. احراز هویت OTP
- ✅ سیستم OTP با هش PBKDF2/SHA256
- ✅ TTL = 5 دقیقه، تعداد تلاش حداکثر 5 بار
- ✅ Rate limiting (60 ثانیه بین درخواست‌ها)
- ✅ ارسال SMS با Kavenegar (با قابلیت Mock)
- ✅ JWT Token (Access: 15min, Refresh: 7days)

### 2. مدل‌ها
- ✅ User (کاربر با phone_number به عنوان username)
- ✅ OTPCode (کدهای یکبار مصرف)
- ✅ Organization (سازمان)
- ✅ OrganizationMember (عضویت با نقش: admin/editor/writer/viewer)
- ✅ Workspace (فضای کاری)
- ✅ Project (پروژه)
- ✅ Prompt (پرامپت‌های قابل استفاده مجدد)
- ✅ Content (محتوا با workflow: draft → in_progress → review → approved/rejected)
- ✅ Version (نسخه‌های محتوا)
- ✅ UsageLog (لاگ مصرف OpenAI API)
- ✅ UsageLimit (محدودیت‌های مصرف)

### 3. APIها
- ✅ `POST /api/auth/otp/request` - درخواست OTP
- ✅ `POST /api/auth/otp/verify` - تأیید OTP و دریافت Token
- ✅ `POST /api/auth/token/refresh` - تمدید Token
- ✅ `GET /api/auth/me` - اطلاعات کاربر جاری
- ✅ CRUD برای Organizations, Workspaces, Projects, Prompts, Contents
- ✅ `POST /api/contents/:id/approve` - تأیید محتوا
- ✅ `POST /api/contents/:id/reject` - رد محتوا

### 4. Permissions
- ✅ IsOrganizationAdmin - فقط ادمین‌های سازمان
- ✅ IsOrganizationMember - اعضای سازمان
- ✅ CanEditContent - ادمین و ادیتور
- ✅ CanCreateContent - ادمین، ادیتور و رایتر
- ✅ CanApproveContent - ادمین و ادیتور

### 5. Celery Tasks
- ✅ `cleanup_expired_otps` - پاکسازی OTPهای منقضی (هر 10 دقیقه)
- ✅ `monthly_usage_reset` - ریست مصرف ماهانه (اول هر ماه)
- ✅ `log_usage_task` - ثبت لاگ مصرف
- ✅ `send_otp_sms_task` - ارسال SMS به صورت async

### 6. تست‌ها
- ✅ تست‌های OTP (issue, verify, TTL, rate limit, max attempts)
- ✅ تست‌های Permissions (نقش‌های مختلف)

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.11+
- PostgreSQL 15
- Redis 7

### نصب با Docker Compose (توصیه می‌شود)

```bash
# از ریشه پروژه
docker-compose up -d
```

### نصب محلی

```bash
# ایجاد محیط مجازی
python -m venv venv
source venv/bin/activate  # در Windows: venv\Scripts\activate

# نصب وابستگی‌ها
pip install -r requirements.txt

# کپی فایل محیطی
cp .env.example .env
# ویرایش .env و تنظیم مقادیر

# اجرای مایگریشن‌ها
python manage.py migrate

# ایجاد سوپریوزر
python manage.py createsuperuser

# اجرای سرور توسعه
python manage.py runserver
```

### اجرای Celery Worker

```bash
# Terminal 1: Celery Worker
celery -A core worker -l info

# Terminal 2: Celery Beat (برای taskهای دوره‌ای)
celery -A core beat -l info
```

## متغیرهای محیطی

مهم‌ترین متغیرها در `.env`:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# OTP
OTP_TTL=300  # 5 minutes
OTP_MAX_ATTEMPTS=5
OTP_RATE_LIMIT=60  # seconds
MOCK_SMS=True  # در production باید False باشد

# Kavenegar
KAVENEGAR_API_KEY=your-key
KAVENEGAR_TEMPLATE=login-otp
KAVENEGAR_SENDER=1000596446

# OpenAI
OPENAI_API_KEY=your-key
OPENAI_DEFAULT_MODEL=gpt-4o-mini
```

## اجرای تست‌ها

```bash
# اجرای همه تست‌ها
python manage.py test

# اجرای تست‌های خاص
python manage.py test tests.test_otp
python manage.py test tests.test_permissions

# با coverage
coverage run --source='.' manage.py test
coverage report
```

## مایگریشن‌ها

```bash
# ساخت مایگریشن‌های جدید
python manage.py makemigrations

# اعمال مایگریشن‌ها
python manage.py migrate

# نمایش وضعیت مایگریشن‌ها
python manage.py showmigrations

# بازگشت به مایگریشن خاص
python manage.py migrate accounts 0001
```

## استفاده از OTP Authentication

### 1. درخواست OTP

```bash
curl -X POST http://localhost:8000/api/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'
```

Response:
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "ttl": 300
}
```

در حالت Mock (MOCK_SMS=True)، کد OTP در لاگ سرور نمایش داده می‌شود.

### 2. تأیید OTP

```bash
curl -X POST http://localhost:8000/api/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789", "code": "123456"}'
```

Response:
```json
{
  "success": true,
  "message": "Successfully logged in",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "user": {
    "id": 1,
    "phone_number": "+989123456789",
    "full_name": null,
    "email": null
  }
}
```

### 3. استفاده از Token

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. تمدید Token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

## ساختار پروژه

```
backend/
├── core/                  # تنظیمات اصلی Django
│   ├── settings.py       # تنظیمات
│   ├── celery.py         # پیکربندی Celery
│   ├── urls.py           # URLهای اصلی
│   └── wsgi.py           # WSGI application
├── accounts/             # اپ کاربران و احراز هویت
│   ├── models.py         # User, OTP, Organization, Workspace
│   ├── serializers.py    # DRF Serializers
│   ├── views.py          # API Views
│   ├── permissions.py    # Custom Permissions
│   ├── services/         # Business Logic
│   │   ├── otp.py        # سرویس OTP
│   │   └── sms.py        # سرویس SMS
│   └── tasks.py          # Celery Tasks
├── contentmgmt/          # اپ مدیریت محتوا
│   ├── models.py         # Project, Prompt, Content, Version
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── ai/                   # اپ AI و Usage Tracking
│   ├── models.py         # UsageLog, UsageLimit
│   ├── tasks.py          # Celery Tasks
│   └── urls.py
├── tests/                # تست‌های واحد
│   ├── test_otp.py       # تست‌های OTP
│   └── test_permissions.py  # تست‌های Permissions
├── manage.py             # Django management script
├── requirements.txt      # وابستگی‌ها
├── Dockerfile            # Docker image
├── entrypoint.sh         # اسکریپت راه‌اندازی
└── .env.example          # نمونه متغیرهای محیطی
```

## پنل ادمین

پنل ادمین Django در آدرس زیر قابل دسترسی است:

```
http://localhost:8000/admin/
```

برای دسترسی، ابتدا یک سوپریوزر ایجاد کنید:

```bash
python manage.py createsuperuser
```

## مستندات API

### Authentication Endpoints

- `POST /api/auth/otp/request` - درخواست کد OTP
- `POST /api/auth/otp/verify` - تأیید OTP و دریافت Token
- `POST /api/auth/token/refresh` - تمدید Access Token
- `GET /api/auth/me` - اطلاعات کاربر احراز هویت شده

### Organization Management

- `GET /api/auth/organizations/` - لیست سازمان‌ها
- `POST /api/auth/organizations/` - ایجاد سازمان
- `GET /api/auth/organizations/:id/` - جزئیات سازمان
- `PUT /api/auth/organizations/:id/` - ویرایش سازمان
- `DELETE /api/auth/organizations/:id/` - حذف سازمان

### Workspace Management

- `GET /api/auth/workspaces/` - لیست فضاهای کاری
- `POST /api/auth/workspaces/` - ایجاد فضای کاری
- `GET /api/auth/workspaces/:id/` - جزئیات فضای کاری
- `PUT /api/auth/workspaces/:id/` - ویرایش فضای کاری
- `DELETE /api/auth/workspaces/:id/` - حذف فضای کاری

### Content Management

- `GET /api/projects/` - لیست پروژه‌ها
- `POST /api/projects/` - ایجاد پروژه
- `GET /api/contents/` - لیست محتواها
- `POST /api/contents/` - ایجاد محتوا
- `POST /api/contents/:id/approve/` - تأیید محتوا
- `POST /api/contents/:id/reject/` - رد محتوا

## Troubleshooting

### مشکل در اتصال به دیتابیس

```bash
# بررسی وضعیت PostgreSQL
docker-compose ps

# مشاهده لاگ‌ها
docker-compose logs db
```

### مشکل در Celery

```bash
# بررسی اتصال به Redis
redis-cli ping

# مشاهده لاگ Celery
docker-compose logs celery
```

### مشکل در ارسال SMS

1. `MOCK_SMS=True` را فعال کنید برای تست بدون ارسال واقعی
2. کد OTP در لاگ کنسول نمایش داده می‌شود
3. بررسی کنید `KAVENEGAR_API_KEY` صحیح باشد

## معیارهای پذیرش

✅ **همه معیارهای پذیرش برآورده شده‌اند:**

1. ✅ اجرای `python manage.py migrate` بدون خطا
2. ✅ OTP از طریق endpointها کار می‌کند (با قابلیت Mock)
3. ✅ تست‌های OTP پاس می‌شوند
4. ✅ تست‌های Permissions پاس می‌شوند
5. ✅ پکیج‌های لازم در requirements.txt
6. ✅ تنظیمات DRF، JWT، Celery، Database کامل
7. ✅ سرویس OTP با PBKDF2 و rate limiting
8. ✅ ادغام Kavenegar برای SMS
9. ✅ مدل‌ها و مایگریشن‌ها
10. ✅ ویوها، سریالایزرها و URLها
11. ✅ Dockerfile و entrypoint.sh

## لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.
