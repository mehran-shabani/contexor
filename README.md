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
DJANGO_SECRET_KEY=your-secret-key-here-generate-random-string
DJANGO_DEBUG=True

# Database
DATABASE_URL=postgres://cg:cg@db:5432/cg

# Redis
REDIS_URL=redis://redis:6379/0

# Kavenegar (ثبت‌نام در https://kavenegar.com)
KAVENEGAR_API_KEY=your-kavenegar-api-key

# OpenAI (دریافت از https://platform.openai.com)
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=gpt-4.1-mini

# JWT
JWT_SIGNING_KEY=your-jwt-signing-key-generate-random-string

# Frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**⚠️ نکته امنیتی:** کلیدهای secret را حتماً تغییر دهید! برای تولید secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

#### 3. Build و اجرای سرویس‌ها

```bash
docker compose up --build
```

این دستور تمام سرویس‌ها را اجرا می‌کند:
- **PostgreSQL** (port 5432)
- **Redis** (port 6379)
- **Django Backend** (port 8000)
- **Celery Worker** (background tasks)
- **Celery Beat** (scheduled tasks)
- **Next.js Frontend** (port 3000)

#### 4. اجرای Migrations و ساخت Superuser

در یک ترمینال جدید:

```bash
# اجرای migrations
docker compose exec backend python manage.py migrate

# ساخت superuser
docker compose exec backend python manage.py createsuperuser
```

#### 5. دسترسی به اپلیکیشن

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1
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
# اجرای تمام tests
python manage.py test

# اجرای tests یک app
python manage.py test accounts

# اجرای با coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

#### Frontend Tests

```bash
# اجرای Jest tests
npm test

# اجرای با coverage
npm test -- --coverage

# E2E tests با Playwright (در صورت نصب)
npx playwright test
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

## 🚢 Production Deployment

### Checklist

- [ ] تنظیم `DEBUG=False`
- [ ] تنظیم `SECRET_KEY` قوی
- [ ] تنظیم `ALLOWED_HOSTS`
- [ ] استفاده از HTTPS
- [ ] تنظیم CORS
- [ ] فعال‌سازی Rate Limiting
- [ ] تنظیم backup خودکار database
- [ ] تنظیم monitoring و logging
- [ ] استفاده از environment variables برای secrets
- [ ] راه‌اندازی Nginx به عنوان reverse proxy
- [ ] تنظیم SSL certificate
- [ ] فعال‌سازی Gunicorn به جای development server

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
