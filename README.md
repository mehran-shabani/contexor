# Contexor - Content Generation Platform

پلتفرم تولید محتوای هوشمند با استفاده از OpenAI API، مدیریت جریان تأیید محتوا و پیگیری مصرف.

## 📋 فهرست مطالب

- [معماری سیستم](#معماری-سیستم)
- [ویژگی‌ها](#ویژگیها)
- [پیش‌نیازها](#پیشنیازها)
- [نصب و راه‌اندازی](#نصب-و-راهاندازی)
- [استفاده](#استفاده)
- [مستندات](#مستندات)
- [توسعه](#توسعه)

---

## 🏗 معماری سیستم

Contexor یک پلتفرم full-stack است که شامل موارد زیر می‌باشد:

### Stack فناوری

**Backend:**
- Django 5.0 + Django REST Framework 3.16
- PostgreSQL 15 (Database)
- Redis 7 (Cache & Message Broker)
- Celery 5.3 (Task Queue)
- djangorestframework-simplejwt (Authentication)

**Frontend:**
- Next.js 15 (App Router)
- React 18
- TypeScript 5
- Tailwind CSS

**External Services:**
- OpenAI API (مدل پیش‌فرض: gpt-4.1-mini)
- Kavenegar (ارسال SMS برای OTP)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (Production)

### معماری

```
┌─────────────┐
│   Next.js   │  (Frontend - Port 3000)
│   Frontend  │
└──────┬──────┘
       │ HTTP/REST
       ↓
┌─────────────┐
│   Django    │  (Backend API - Port 8000)
│   REST API  │
└──────┬──────┘
       │
       ├──> PostgreSQL 15 (Database - Port 5432)
       ├──> Redis 7 (Cache/Queue - Port 6379)
       └──> Celery Workers (Async Tasks)
              ├──> OpenAI API (Content Generation)
              └──> Kavenegar API (OTP SMS)
```

برای جزئیات بیشتر: [docs/01-architecture.md](./docs/01-architecture.md)

---

## ✨ ویژگی‌ها

### 🔐 احراز هویت
- ورود با شماره تلفن و OTP
- احراز هویت JWT-based
- مدیریت access و refresh tokens

### 🏢 مدیریت سازمان
- سازمان‌های چندکاربره
- فضاهای کاری (Workspaces)
- کنترل دسترسی سطح‌بندی شده (Admin/Editor/Viewer)

### 📝 تولید محتوا
- پرامپت‌های قابل استفاده مجدد
- تولید محتوا با OpenAI API
- جریان تأیید (Draft → In Progress → Review → Approved/Rejected)
- ذخیره نسخه‌های مختلف محتوا
- تشخیص PII (اطلاعات حساس)

### 📊 پیگیری مصرف
- ثبت تمام درخواست‌های OpenAI
- محدودیت مصرف ماهانه (تعداد request، توکن، هزینه)
- داشبورد مصرف (User/Workspace/Organization)
- تخمین هزینه real-time

---

## 📦 پیش‌نیازها

قبل از نصب، اطمینان حاصل کنید که موارد زیر نصب شده‌اند:

- **Docker** (نسخه 20.10+)
- **Docker Compose** (نسخه 2.0+)
- **Git**

برای توسعه بدون Docker:
- **Python 3.11+**
- **Node.js 20+**
- **PostgreSQL 15**
- **Redis 7**

---

## 🚀 نصب و راه‌اندازی

### روش 1: استفاده از Docker Compose (توصیه می‌شود)

#### 1. دانلود پروژه

```bash
git clone <repository-url>
cd contexor
```

#### 2. تنظیم Environment Variables

```bash
cp .env.example .env
```

فایل `.env` را ویرایش کنید و مقادیر زیر را تنظیم کنید:

```env
# Django
SECRET_KEY=your-secret-key-here-generate-random-string
DEBUG=True

# Database
DATABASE_URL=postgresql://cg:cg@db:5432/cg

# Redis
REDIS_URL=redis://redis:6379/0

# Kavenegar SMS (ثبت‌نام در https://kavenegar.com)
KAVENEGAR_API_KEY=your-kavenegar-api-key
KAVENEGAR_TEMPLATE=login-otp
KAVENEGAR_SENDER=1000596446
MOCK_SMS=True  # Set to False in production

# OpenAI (دریافت از https://platform.openai.com)
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=gpt-4o-mini

# AI Usage Limits & Budget
AI_MONTHLY_BUDGET_USD=100.0
AI_WORKSPACE_MONTHLY_BUDGET_USD=100.0
AI_USER_MONTHLY_BUDGET_USD=50.0
DEFAULT_MONTHLY_TOKEN_LIMIT=1000000
DEFAULT_MONTHLY_COST_LIMIT=100.0
DEFAULT_MONTHLY_REQUEST_LIMIT=1000

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**⚠️ نکته امنیتی:** کلیدهای secret را حتماً تغییر دهید! برای تولید secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

#### 3. Build و اجرای سرویس‌ها

```bash
# Build و اجرا به صورت جدا
docker compose up --build -d

# مشاهده logs
docker compose logs -f
```

این دستور تمام سرویس‌ها را اجرا می‌کند:
- **db** (PostgreSQL 15 - port 5432) - با healthcheck
- **redis** (Redis 7 - port 6379) - با healthcheck  
- **backend** (Django API - port 8000) - با healthcheck
- **worker** (Celery Worker - background tasks)
- **beat** (Celery Beat - scheduled tasks)
- **frontend** (Next.js - port 3000)

#### 4. اجرای Migrations و ساخت Superuser

صبر کنید تا همه healthcheck ها سبز شوند (حدود 30 ثانیه)، سپس:

```bash
# اجرای migrations
docker compose exec backend python manage.py migrate

# ساخت superuser (اختیاری)
docker compose exec backend python manage.py createsuperuser
```

#### 5. بررسی وضعیت سرویس‌ها

```bash
# بررسی وضعیت healthcheck ها
docker compose ps

# اجرای smoke tests
./scripts/smoke.sh

# تست backend
./scripts/test_backend.sh

# Lint check
./scripts/lint.sh
```

#### 6. دسترسی به اپلیکیشن

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/
- **Health Check:** http://localhost:8000/health/
- **Django Admin:** http://localhost:8000/admin

### روش 2: نصب Local (بدون Docker)

#### Backend Setup

```bash
cd backend

# ساخت virtual environment
python -m venv venv
source venv/bin/activate  # در Windows: venv\Scripts\activate

# نصب dependencies
pip install -r requirements.txt

# تنظیم environment variables
cp ../.env.example ../.env
# فایل .env را ویرایش کنید

# اجرای migrations
python manage.py migrate

# ساخت superuser
python manage.py createsuperuser

# اجرای سرور
python manage.py runserver
```

در ترمینال‌های جداگانه:

```bash
# Celery Worker
celery -A core worker -l info

# Celery Beat
celery -A core beat -l info
```

#### Frontend Setup

```bash
cd frontend

# نصب dependencies
npm install

# اجرای سرور توسعه
npm run dev
```

---

## 💻 استفاده

### 1. ثبت‌نام و ورود

1. به http://localhost:3000/login بروید
2. شماره تلفن خود را وارد کنید
3. کد OTP ارسال شده به تلفن را وارد کنید
4. وارد داشبورد می‌شوید

### 2. ساخت سازمان و Workspace

```bash
# از طریق API
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "شرکت نمونه",
    "slug": "company-demo"
  }'

curl -X POST http://localhost:8000/api/v1/organizations/1/workspaces \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marketing Team",
    "slug": "marketing"
  }'
```

### 3. ساخت Prompt

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "پست وبلاگ SEO",
    "category": "blog",
    "prompt_template": "یک پست وبلاگ {word_count} کلمه‌ای درباره {topic} بنویس",
    "variables": ["word_count", "topic"],
    "workspace": 1
  }'
```

### 4. تولید محتوا

```bash
# ساخت محتوای جدید
curl -X POST http://localhost:8000/api/v1/contents \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "بهترین محصولات پاییزی",
    "project": 1,
    "prompt": 1,
    "prompt_variables": {
      "word_count": "800",
      "topic": "محصولات پاییزی"
    }
  }'

# درخواست تولید
curl -X POST http://localhost:8000/api/v1/contents/1/generate \
  -H "Authorization: Bearer <access_token>"

# دریافت محتوا
curl http://localhost:8000/api/v1/contents/1 \
  -H "Authorization: Bearer <access_token>"
```

### 5. بررسی مصرف

```bash
curl http://localhost:8000/api/v1/usage/summary?scope=user&month=2025-10 \
  -H "Authorization: Bearer <access_token>"
```

---

## 📚 مستندات

### مستندات کامل

- **[معماری سیستم](./docs/01-architecture.md)** - نمودارها، stack، و جریان‌های اصلی
- **[API Contracts](./docs/02-api-contracts.md)** - تمام endpointها با مثال request/response
- **[Data Models](./docs/03-data-models.md)** - مدل‌های PostgreSQL و schema

### API Documentation

پس از اجرای سرور، می‌توانید به API documentation دسترسی داشته باشید:

- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/

### نمونه‌های API

#### Authentication

```bash
# درخواست OTP
POST /api/v1/auth/otp/request
{
  "phone_number": "+989123456789"
}

# تأیید OTP
POST /api/v1/auth/otp/verify
{
  "phone_number": "+989123456789",
  "code": "123456"
}
# Response: { "access": "...", "refresh": "...", "user": {...} }
```

#### Content Management

```bash
# لیست محتواها
GET /api/v1/contents?status=approved&project=1

# تأیید محتوا
POST /api/v1/contents/1/approve
{
  "notes": "محتوا تأیید شد"
}
```

---

## 🐛 Troubleshooting

### مشکلات رایج و راه‌حل‌ها

#### ❌ Backend به Database متصل نمی‌شود

**علائم:**
```
django.db.utils.OperationalError: could not connect to server
```

**راه‌حل:**
1. بررسی کنید که سرویس db در حال اجرا است:
   ```bash
   docker compose ps db
   ```
2. صبر کنید تا healthcheck سبز شود:
   ```bash
   docker compose logs db
   ```
3. `DATABASE_URL` را در `.env` بررسی کنید (باید `db` به جای `localhost` باشد)

#### ❌ Redis Connection Error

**علائم:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**راه‌حل:**
1. بررسی کنید Redis در حال اجرا است:
   ```bash
   docker compose ps redis
   ```
2. `REDIS_URL` را بررسی کنید: باید `redis://redis:6379/0` باشد (نه `localhost`)

#### ❌ CORS Error در Frontend

**علائم:**
```
Access to fetch has been blocked by CORS policy
```

**راه‌حل:**
1. `CORS_ALLOWED_ORIGINS` را در `.env` بررسی کنید
2. آدرس frontend را به لیست اضافه کنید:
   ```env
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
3. Backend را restart کنید:
   ```bash
   docker compose restart backend
   ```

#### ❌ Frontend به Backend متصل نمی‌شود

**راه‌حل:**
1. `NEXT_PUBLIC_BACKEND_URL` را در `.env` بررسی کنید
2. مطمئن شوید backend healthcheck سبز است:
   ```bash
   curl http://localhost:8000/health/
   ```

#### ❌ Celery Worker کار نمی‌کند

**راه‌حل:**
1. Logs را بررسی کنید:
   ```bash
   docker compose logs worker
   ```
2. Redis connection را تست کنید
3. Worker را restart کنید:
   ```bash
   docker compose restart worker
   ```

#### ❌ Rate Limiting/Throttling Issues

**علائم:**
```
HTTP 429 Too Many Requests
```

**راه‌حل:**
- این رفتار عادی است برای محافظت از API
- صبر کنید چند دقیقه و دوباره تلاش کنید
- یا throttle rates را در `settings.py` تنظیم کنید

#### ❌ AI Budget Exceeded (402 Error)

**علائم:**
```
HTTP 402 Payment Required - Monthly budget exceeded
```

**راه‌حل:**
1. بررسی مصرف فعلی:
   ```bash
   curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/ai/usage/summary/
   ```
2. افزایش budget در `.env`:
   ```env
   AI_WORKSPACE_MONTHLY_BUDGET_USD=200.0
   ```
3. یا صبر تا اول ماه بعد

#### ❌ Missing Environment Variables

**راه‌حل:**
1. فایل `.env` را از `.env.example` بسازید
2. تمام متغیرهای ضروری را پر کنید:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `REDIS_URL`
   - `OPENAI_API_KEY`

#### 🔄 Reset کامل سیستم

اگر مشکلات متعددی دارید:

```bash
# پاک کردن همه چیز
docker compose down -v

# پاک کردن images
docker compose down --rmi all

# Build و اجرای مجدد
docker compose up --build

# اجرای migrations
docker compose exec backend python manage.py migrate
```

---

## 🛠 توسعه

### ساختار پروژه

```
contexor/
├── backend/                 # Django backend
│   ├── core/               # تنظیمات اصلی Django
│   │   ├── settings.py
│   │   ├── celery.py
│   │   └── urls.py
│   ├── accounts/           # احراز هویت و کاربران
│   │   ├── models.py
│   │   ├── views.py
│   │   └── serializers.py
│   ├── contentmgmt/        # مدیریت محتوا
│   │   ├── models.py
│   │   ├── views.py
│   │   └── services.py
│   ├── ai/                 # سرویس‌های AI
│   │   ├── service.py      # OpenAI integration
│   │   ├── tasks.py        # Celery tasks
│   │   └── pii.py          # PII detection
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/               # Next.js frontend
│   ├── app/               # App Router
│   │   ├── (auth)/
│   │   │   └── login/
│   │   ├── (dashboard)/
│   │   │   ├── projects/
│   │   │   ├── contents/
│   │   │   └── usage/
│   │   └── layout.tsx
│   ├── components/        # React components
│   │   ├── ui/
│   │   └── forms/
│   ├── lib/
│   │   ├── api.ts        # API client
│   │   └── auth.ts       # Auth utilities
│   └── package.json
│
├── docs/                  # مستندات
│   ├── 01-architecture.md
│   ├── 02-api-contracts.md
│   └── 03-data-models.md
│
├── docker-compose.yml
├── .env.example
└── README.md
```

### دستورات مفید

#### Backend

```bash
# اجرای migrations
python manage.py migrate

# ساخت migration جدید
python manage.py makemigrations

# اجرای tests
python manage.py test

# باز کردن Django shell
python manage.py shell

# جمع‌آوری static files
python manage.py collectstatic

# ساخت data نمونه (seed)
python manage.py loaddata fixtures/sample_data.json
```

#### Frontend

```bash
# نصب dependencies
npm install

# اجرای development server
npm run dev

# Build برای production
npm run build

# اجرای production server
npm start

# Linting
npm run lint

# Type checking
npm run type-check
```

#### Docker

```bash
# بالا آوردن سرویس‌ها
docker compose up

# اجرا در background
docker compose up -d

# مشاهده logs
docker compose logs -f

# مشاهده logs یک سرویس
docker compose logs -f backend

# پایین آوردن سرویس‌ها
docker compose down

# پایین آوردن همراه با volumes
docker compose down -v

# Rebuild سرویس‌ها
docker compose up --build

# اجرای دستور در container
docker compose exec backend python manage.py migrate
```

### Debugging

#### Backend Debugging

```python
# استفاده از IPython
import IPython; IPython.embed()

# Django Debug Toolbar (در development)
# در settings.py اضافه کنید:
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

#### Frontend Debugging

```typescript
// استفاده از console.log
console.log('Debug:', data);

// استفاده از React DevTools
// نصب extension برای Chrome/Firefox
```

### Testing

#### Backend Tests

```bash
# روش سریع - استفاده از script
./scripts/test_backend.sh

# یا manual
cd backend
python manage.py test

# اجرای tests یک app
python manage.py test accounts

# تست‌های خاص
python manage.py test tests.test_throttling
python manage.py test tests.test_audit_log
python manage.py test tests.test_budget_enforcement

# اجرای با coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

#### Frontend Tests

```bash
# استفاده از script
./scripts/test_frontend.sh

# یا manual
cd frontend
npm test

# اجرای با coverage
npm test -- --coverage

# E2E tests با Playwright
npx playwright test
```

#### Quality Scripts

پروژه شامل اسکریپت‌های کیفی در دایرکتوری `./scripts/` است:

```bash
# اجرای تست‌های backend
./scripts/test_backend.sh

# اجرای تست‌های frontend
./scripts/test_frontend.sh

# Linting (flake8 + eslint)
./scripts/lint.sh

# Smoke tests (health checks)
./scripts/smoke.sh
```

---

## 🔧 Configuration

### Environment Variables

متغیرهای محیطی مهم:

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | - |
| `DJANGO_DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `KAVENEGAR_API_KEY` | Kavenegar API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_DEFAULT_MODEL` | مدل پیش‌فرض OpenAI | `gpt-4.1-mini` |
| `JWT_ACCESS_TOKEN_LIFETIME` | عمر access token (دقیقه) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME` | عمر refresh token (دقیقه) | `1440` |

### Django Settings

فایل‌های تنظیمات مختلف برای environmentهای مختلف:

```python
# core/settings/base.py       - تنظیمات مشترک
# core/settings/development.py - تنظیمات development
# core/settings/production.py  - تنظیمات production
```

استفاده:

```bash
# Development
export DJANGO_SETTINGS_MODULE=core.settings.development

# Production
export DJANGO_SETTINGS_MODULE=core.settings.production
```

---

## ✅ چک‌لیست پذیرش (Acceptance Checklist)

این چک‌لیست برای تأیید عملکرد صحیح سیستم پس از deployment استفاده می‌شود:

### 1. Infrastructure & Services

```bash
# همه سرویس‌ها باید healthy باشند
docker compose ps

# خروجی باید نشان دهد:
# - db (healthy)
# - redis (healthy)
# - backend (healthy)
# - worker (running)
# - beat (running)
# - frontend (running)
```

### 2. Health Checks

```bash
# تست health endpoint
curl http://localhost:8000/health/
# انتظار: {"status": "healthy", "services": {"database": "ok", "cache": "ok"}}

# اجرای smoke tests
./scripts/smoke.sh
# همه تست‌ها باید سبز شوند (✓)
```

### 3. Authentication & OTP

```bash
# درخواست OTP
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789"}'

# انتظار: HTTP 200 یا 429 (اگر rate limit)
# پیام success یا retry_after

# تأیید OTP (با کد mock در development)
curl -X POST http://localhost:8000/api/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789", "code": "123456"}'

# انتظار: HTTP 200 با access و refresh token
```

### 4. Project & Content Management

**از طریق Frontend:**
1. ورود به http://localhost:3000/login با OTP
2. ایجاد Organization جدید
3. ایجاد Workspace
4. ایجاد Project
5. ایجاد Prompt template
6. ایجاد Content

**یا از طریق API:**
```bash
TOKEN="your-access-token"

# ایجاد Organization
curl -X POST http://localhost:8000/api/organizations/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Org", "slug": "test-org"}'

# ایجاد Project
curl -X POST http://localhost:8000/api/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "workspace": 1, "slug": "test-project"}'

# ایجاد Content
curl -X POST http://localhost:8000/api/contents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Content", "project": 1, "prompt": 1}'
```

### 5. AI Content Generation

```bash
# درخواست تولید محتوا
curl -X POST http://localhost:8000/api/contents/1/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "draft",
    "topic": "مزایای هوش مصنوعی",
    "tone": "حرفه‌ای",
    "audience": "کارآفرینان",
    "min_words": 800
  }'

# انتظار: HTTP 202 با job_id
# یا HTTP 402 اگر budget تجاوز شده
```

### 6. Usage Tracking & Budget

```bash
# بررسی مصرف
curl http://localhost:8000/api/ai/usage/summary/ \
  -H "Authorization: Bearer $TOKEN"

# انتظار: آمار tokens، cost، و requests

# تست budget enforcement (با limit پایین):
# 1. ایجاد UsageLimit با cost_limit=1.0
# 2. ایجاد UsageLog با cost > 1.0
# 3. تلاش برای generate
# انتظار: HTTP 402 Payment Required
```

### 7. Content Structure (H2/H3)

بررسی کنید که محتوای تولید شده دارای ساختار مناسب است:
- عنوان‌های H2 برای بخش‌های اصلی
- عنوان‌های H3 برای زیربخش‌ها
- فرمت Markdown صحیح

### 8. Rate Limiting & Throttling

```bash
# تست OTP throttle (5/min per IP)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/otp/request/ \
    -H "Content-Type: application/json" \
    -d '{"phone_number": "+98912'$i'456789"}'
  echo ""
done
# درخواست 6+ باید 429 برگرداند

# تست content generate throttle (10/min per user)
# تکرار 11+ بار با user احراز هویت شده
# انتظار: HTTP 429 در درخواست 11+
```

### 9. Audit Logging

```bash
# بررسی audit logs
docker compose exec backend python manage.py shell
```

```python
from ai.models import AuditLog
from contentmgmt.models import Content

# نمایش آخرین audit logs
logs = AuditLog.objects.all()[:10]
for log in logs:
    print(f"{log.timestamp} - {log.action} - {log.user} - {log.content}")

# بررسی approve event
content = Content.objects.filter(status='approved').first()
if content:
    approve_logs = content.audit_logs.filter(action='approved')
    print(f"Approve logs: {approve_logs.count()}")
```

### 10. Worker & Beat

```bash
# بررسی worker logs
docker compose logs worker --tail=50

# بررسی beat logs
docker compose logs beat --tail=50

# تست async task
# محتوای generate شده باید در پس‌زمینه پردازش شود
```

### 11. Testing & Quality

```bash
# اجرای تمام تست‌ها
./scripts/test_backend.sh
# انتظار: All tests passed

# Linting
./scripts/lint.sh
# انتظار: No critical errors

# Smoke tests
./scripts/smoke.sh
# انتظار: All checks ✓
```

### ✅ معیارهای موفقیت

برای تأیید نهایی، موارد زیر باید برقرار باشند:

- [x] `docker compose up -d` بدون خطا اجرا می‌شود
- [x] همه healthcheck ها سبز هستند (db, redis, backend)
- [x] OTP login کار می‌کند (درخواست + تأیید)
- [x] ایجاد project و content موفقیت‌آمیز است
- [x] Content generation درخواست می‌شود و job ایجاد می‌شود
- [x] Usage و cost ثبت می‌شوند
- [x] محتوای تولید شده دارای H2/H3 است
- [x] Throttling اعمال می‌شود (OTP: 5/min, Generate: 10/min)
- [x] Budget enforcement کار می‌کند (402 در صورت تجاوز)
- [x] Audit logs برای create/approve ثبت می‌شوند
- [x] Worker و Beat در حال اجرا هستند
- [x] Frontend به backend متصل است
- [x] Smoke tests موفق هستند

---

## 🚢 Production Deployment

### Checklist

- [ ] تنظیم `DEBUG=False`
- [ ] تنظیم `SECRET_KEY` قوی (50+ characters random)
- [ ] تنظیم `ALLOWED_HOSTS`
- [ ] استفاده از HTTPS
- [ ] تنظیم `CORS_ALLOWED_ORIGINS` برای production domain
- [ ] تنظیم `CSRF_TRUSTED_ORIGINS`
- [ ] فعال‌سازی Rate Limiting (پیش‌فرض فعال است)
- [ ] تنظیم AI budgets مناسب
- [ ] تنظیم backup خودکار database
- [ ] تنظیم monitoring و logging
- [ ] استفاده از environment variables برای secrets
- [ ] راه‌اندازی Nginx به عنوان reverse proxy
- [ ] تنظیم SSL certificate
- [ ] فعال‌سازی Gunicorn به جای development server
- [ ] `MOCK_SMS=False` و تنظیم Kavenegar API
- [ ] تنظیم `OPENAI_API_KEY` معتبر

### Docker Production

```bash
# استفاده از production docker-compose
docker compose -f docker-compose.prod.yml up -d
```

---

## 🤝 مشارکت

برای مشارکت در پروژه:

1. Fork کنید
2. یک branch جدید بسازید (`git checkout -b feature/amazing-feature`)
3. تغییرات خود را commit کنید (`git commit -m 'Add amazing feature'`)
4. Push کنید (`git push origin feature/amazing-feature`)
5. یک Pull Request باز کنید

---

## 📄 License

این پروژه تحت لایسنس MIT منتشر شده است.

---

## 📞 پشتیبانی

در صورت مواجهه با مشکل:

1. [Issues](https://github.com/yourrepo/contexor/issues) را بررسی کنید
2. مستندات را مطالعه کنید
3. یک issue جدید باز کنید

---

## 🙏 تشکر

از تمامی کسانی که در ساخت این پروژه مشارکت داشته‌اند، تشکر می‌کنیم.

---

**نکته:** این پروژه در حال توسعه است و ممکن است تغییرات breaking داشته باشد. برای استفاده در production، از نسخه‌های stable استفاده کنید.
