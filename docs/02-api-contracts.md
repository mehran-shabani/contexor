# قراردادهای API - Contexor

## مقدمه

این سند تمامی APIهای سیستم Contexor را با جزئیات کامل شرح می‌دهد. تمامی APIها از Django REST Framework پیاده‌سازی شده‌اند و از فرمت JSON استفاده می‌کنند.

**Base URL (Development):** `http://localhost:8000/api/v1`

**Authentication:** 
- اکثر APIها نیاز به احراز هویت دارند
- از JWT Token استفاده می‌شود
- Header مورد نیاز: `Authorization: Bearer <access_token>`

**Response Format:**
```json
{
  "success": true/false,
  "data": {...},
  "error": "error message" (در صورت خطا)
}
```

---

## 1. Authentication APIs

### 1.1. درخواست OTP

**Endpoint:** `POST /api/v1/auth/otp/request`

**Description:** درخواست ارسال کد OTP به شماره تلفن همراه

**Authentication:** ❌ No (Public)

**Request Body:**
```json
{
  "phone_number": "+989123456789"
}
```

**Validation Rules:**
- `phone_number`: Required, must be valid Iranian mobile number format (+989xxxxxxxxx)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "phone_number": "+989123456789",
    "ttl": 120,
    "message": "کد تأیید به شماره شما ارسال شد"
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "شماره تلفن نامعتبر است",
  "errors": {
    "phone_number": ["Enter a valid phone number."]
  }
}
```

**Response (429 Too Many Requests):**
```json
{
  "success": false,
  "error": "تعداد درخواست‌های شما بیش از حد مجاز است. لطفا بعدا تلاش کنید."
}
```

**Implementation Notes:**
- کد OTP 6 رقمی تولید می‌شود
- TTL در Redis: 120 ثانیه
- Rate limiting: 3 requests per 5 minutes per phone number
- Celery task برای ارسال SMS به Kavenegar

---

### 1.2. تأیید OTP و دریافت Token

**Endpoint:** `POST /api/v1/auth/otp/verify`

**Description:** تأیید کد OTP و دریافت access/refresh tokens

**Authentication:** ❌ No (Public)

**Request Body:**
```json
{
  "phone_number": "+989123456789",
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "phone_number": "+989123456789",
      "full_name": "علی احمدی",
      "is_active": true,
      "date_joined": "2025-10-01T10:30:00Z"
    }
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "کد تأیید نامعتبر یا منقضی شده است"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "شماره تلفن یافت نشد"
}
```

**Implementation Notes:**
- اگر کاربر جدید باشد، حساب کاربری ساخته می‌شود
- Token lifetime: Access 60min, Refresh 24h

---

### 1.3. تمدید Token

**Endpoint:** `POST /api/v1/auth/token/refresh`

**Description:** تمدید access token با استفاده از refresh token

**Authentication:** ❌ No (Public)

**Request Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "Refresh token نامعتبر یا منقضی شده است"
}
```

---

### 1.4. خروج از سیستم

**Endpoint:** `POST /api/v1/auth/logout`

**Description:** باطل کردن refresh token

**Authentication:** ✅ Yes (Bearer Token)

**Request Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "با موفقیت از سیستم خارج شدید"
}
```

---

## 2. User & Organization APIs

### 2.1. دریافت پروفایل کاربر

**Endpoint:** `GET /api/v1/users/me`

**Description:** دریافت اطلاعات کاربر جاری

**Authentication:** ✅ Yes (Bearer Token)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "phone_number": "+989123456789",
    "full_name": "علی احمدی",
    "email": "ali@example.com",
    "is_active": true,
    "date_joined": "2025-10-01T10:30:00Z",
    "organizations": [
      {
        "id": 1,
        "name": "شرکت نمونه",
        "role": "admin"
      }
    ]
  }
}
```

---

### 2.2. بروزرسانی پروفایل

**Endpoint:** `PATCH /api/v1/users/me`

**Description:** ویرایش اطلاعات کاربر

**Authentication:** ✅ Yes (Bearer Token)

**Request Body:**
```json
{
  "full_name": "علی احمدی",
  "email": "ali.new@example.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "phone_number": "+989123456789",
    "full_name": "علی احمدی",
    "email": "ali.new@example.com"
  }
}
```

---

### 2.3. لیست سازمان‌ها

**Endpoint:** `GET /api/v1/organizations`

**Description:** دریافت لیست سازمان‌هایی که کاربر عضو آن‌هاست

**Authentication:** ✅ Yes (Bearer Token)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "شرکت نمونه",
      "slug": "company-demo",
      "created_at": "2025-09-01T10:00:00Z",
      "role": "admin",
      "workspaces_count": 3,
      "members_count": 5
    }
  ]
}
```

---

### 2.4. ایجاد سازمان

**Endpoint:** `POST /api/v1/organizations`

**Description:** ساخت سازمان جدید

**Authentication:** ✅ Yes (Bearer Token)

**Request Body:**
```json
{
  "name": "شرکت جدید",
  "slug": "new-company"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "شرکت جدید",
    "slug": "new-company",
    "created_at": "2025-10-05T14:30:00Z",
    "role": "admin"
  }
}
```

---

### 2.5. لیست Workspaces

**Endpoint:** `GET /api/v1/organizations/{org_id}/workspaces`

**Description:** دریافت لیست فضاهای کاری در یک سازمان

**Authentication:** ✅ Yes (Bearer Token)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Marketing Team",
      "slug": "marketing",
      "organization": 1,
      "created_at": "2025-09-15T09:00:00Z",
      "projects_count": 5
    }
  ]
}
```

---

### 2.6. ایجاد Workspace

**Endpoint:** `POST /api/v1/organizations/{org_id}/workspaces`

**Description:** ساخت فضای کاری جدید

**Authentication:** ✅ Yes (Bearer Token - باید admin سازمان باشد)

**Request Body:**
```json
{
  "name": "Content Team",
  "slug": "content"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Content Team",
    "slug": "content",
    "organization": 1,
    "created_at": "2025-10-05T15:00:00Z"
  }
}
```

---

## 3. Prompt APIs

### 3.1. لیست Promptها

**Endpoint:** `GET /api/v1/prompts`

**Description:** دریافت لیست پرامپت‌های قابل استفاده

**Authentication:** ✅ Yes (Bearer Token)

**Query Parameters:**
- `workspace` (optional): فیلتر بر اساس workspace
- `category` (optional): فیلتر بر اساس دسته‌بندی
- `search` (optional): جستجو در عنوان و محتوا

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "پست وبلاگ SEO",
      "category": "blog",
      "prompt_template": "یک پست وبلاگ {word_count} کلمه‌ای درباره {topic} بنویس که برای SEO بهینه باشد.",
      "variables": ["word_count", "topic"],
      "workspace": 1,
      "is_public": false,
      "created_at": "2025-09-20T10:00:00Z",
      "created_by": {
        "id": 1,
        "full_name": "علی احمدی"
      }
    }
  ]
}
```

---

### 3.2. جزئیات Prompt

**Endpoint:** `GET /api/v1/prompts/{id}`

**Description:** دریافت جزئیات یک پرامپت

**Authentication:** ✅ Yes (Bearer Token)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "پست وبلاگ SEO",
    "category": "blog",
    "prompt_template": "یک پست وبلاگ {word_count} کلمه‌ای درباره {topic} بنویس که برای SEO بهینه باشد.",
    "variables": ["word_count", "topic"],
    "workspace": 1,
    "is_public": false,
    "usage_count": 45,
    "created_at": "2025-09-20T10:00:00Z"
  }
}
```

---

### 3.3. ایجاد Prompt

**Endpoint:** `POST /api/v1/prompts`

**Description:** ساخت پرامپت جدید

**Authentication:** ✅ Yes (Bearer Token)

**Request Body:**
```json
{
  "title": "توضیحات محصول",
  "category": "ecommerce",
  "prompt_template": "یک توضیحات جذاب برای محصول {product_name} با قیمت {price} تومان بنویس.",
  "variables": ["product_name", "price"],
  "workspace": 1,
  "is_public": false
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "title": "توضیحات محصول",
    "category": "ecommerce",
    "prompt_template": "یک توضیحات جذاب برای محصول {product_name} با قیمت {price} تومان بنویس.",
    "variables": ["product_name", "price"],
    "workspace": 1,
    "is_public": false,
    "created_at": "2025-10-05T16:00:00Z"
  }
}
```

---

## 4. Project APIs

### 4.1. لیست پروژه‌ها

**Endpoint:** `GET /api/v1/projects`

**Description:** دریافت لیست پروژه‌ها

**Authentication:** ✅ Yes (Bearer Token)

**Query Parameters:**
- `workspace` (required): شناسه workspace

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "کمپین پاییز",
      "slug": "fall-campaign",
      "description": "محتوای کمپین پاییزه",
      "workspace": 1,
      "created_at": "2025-09-25T10:00:00Z",
      "contents_count": 12
    }
  ]
}
```

---

### 4.2. ایجاد پروژه

**Endpoint:** `POST /api/v1/projects`

**Description:** ساخت پروژه جدید

**Authentication:** ✅ Yes (Bearer Token)

**Request Body:**
```json
{
  "name": "کمپین زمستان",
  "slug": "winter-campaign",
  "description": "محتوای کمپین زمستانه",
  "workspace": 1
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "کمپین زمستان",
    "slug": "winter-campaign",
    "description": "محتوای کمپین زمستانه",
    "workspace": 1,
    "created_at": "2025-10-05T16:30:00Z"
  }
}
```

---

## 5. Content APIs

### 5.1. لیست محتواها

**Endpoint:** `GET /api/v1/contents`

**Description:** دریافت لیست محتواها

**Authentication:** ✅ Yes (Bearer Token)

**Query Parameters:**
- `project` (optional): فیلتر بر اساس پروژه
- `status` (optional): فیلتر بر اساس وضعیت (draft, in_progress, review, approved, rejected)
- `search` (optional): جستجو در عنوان
- `page` (optional, default: 1): شماره صفحه
- `page_size` (optional, default: 20): تعداد آیتم در صفحه

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "count": 45,
    "next": "http://localhost:8000/api/v1/contents?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "title": "بهترین محصولات پاییزی",
        "project": {
          "id": 1,
          "name": "کمپین پاییز"
        },
        "prompt": {
          "id": 1,
          "title": "پست وبلاگ SEO"
        },
        "status": "approved",
        "word_count": 850,
        "created_at": "2025-10-01T10:00:00Z",
        "updated_at": "2025-10-02T14:30:00Z",
        "created_by": {
          "id": 1,
          "full_name": "علی احمدی"
        }
      }
    ]
  }
}
```

---

### 5.2. ایجاد محتوا

**Endpoint:** `POST /api/v1/contents`

**Description:** ساخت محتوای جدید (وضعیت اولیه: DRAFT)

**Authentication:** ✅ Yes (Bearer Token)

**Request Body:**
```json
{
  "title": "معرفی محصول جدید",
  "project": 1,
  "prompt": 2,
  "prompt_variables": {
    "product_name": "کفش ورزشی ایکس",
    "price": "۲,۵۰۰,۰۰۰"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "title": "معرفی محصول جدید",
    "project": 1,
    "prompt": 2,
    "prompt_variables": {
      "product_name": "کفش ورزشی ایکس",
      "price": "۲,۵۰۰,۰۰۰"
    },
    "status": "draft",
    "body": null,
    "created_at": "2025-10-05T17:00:00Z"
  }
}
```

---

### 5.3. جزئیات محتوا

**Endpoint:** `GET /api/v1/contents/{id}`

**Description:** دریافت جزئیات کامل یک محتوا

**Authentication:** ✅ Yes (Bearer Token)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "بهترین محصولات پاییزی",
    "project": {
      "id": 1,
      "name": "کمپین پاییز"
    },
    "prompt": {
      "id": 1,
      "title": "پست وبلاگ SEO",
      "prompt_template": "یک پست وبلاگ {word_count} کلمه‌ای درباره {topic} بنویس..."
    },
    "prompt_variables": {
      "word_count": "800",
      "topic": "محصولات پاییزی"
    },
    "status": "approved",
    "body": "# بهترین محصولات پاییزی\n\nفصل پاییز با خود محصولات جذابی را به همراه دارد...",
    "word_count": 850,
    "has_pii": false,
    "pii_warnings": [],
    "metadata": {
      "model": "gpt-4.1-mini",
      "tokens_used": 1200,
      "generation_time": 3.5
    },
    "created_at": "2025-10-01T10:00:00Z",
    "updated_at": "2025-10-02T14:30:00Z",
    "approved_at": "2025-10-02T14:30:00Z",
    "created_by": {
      "id": 1,
      "full_name": "علی احمدی"
    }
  }
}
```

---

### 5.4. بروزرسانی محتوا

**Endpoint:** `PATCH /api/v1/contents/{id}`

**Description:** ویرایش محتوا (فقط در وضعیت DRAFT و REVIEW)

**Authentication:** ✅ Yes (Bearer Token)

**Request Body:**
```json
{
  "title": "عنوان جدید",
  "body": "محتوای ویرایش شده..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "title": "عنوان جدید",
    "body": "محتوای ویرایش شده...",
    "updated_at": "2025-10-05T17:30:00Z"
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "محتوای تأیید شده قابل ویرایش نیست"
}
```

---

### 5.5. درخواست تولید محتوا

**Endpoint:** `POST /api/v1/contents/{id}/generate`

**Description:** شروع فرآیند تولید محتوا با OpenAI (async)

**Authentication:** ✅ Yes (Bearer Token)

**Request Body (optional):**
```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "content_id": 2,
    "task_id": "abc123-def456-ghi789",
    "status": "in_progress",
    "message": "تولید محتوا در حال انجام است. لطفا منتظر بمانید."
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "محتوا باید در وضعیت DRAFT باشد"
}
```

**Response (429 Too Many Requests):**
```json
{
  "success": false,
  "error": "سقف مصرف ماهانه شما تمام شده است"
}
```

**Implementation Notes:**
- وضعیت محتوا به IN_PROGRESS تغییر می‌کند
- Celery task برای تولید محتوا queue می‌شود
- Frontend باید polling کند یا از WebSocket استفاده کند

---

### 5.6. تأیید محتوا

**Endpoint:** `POST /api/v1/contents/{id}/approve`

**Description:** تأیید محتوا و تغییر وضعیت به APPROVED

**Authentication:** ✅ Yes (Bearer Token - نیاز به permission)

**Request Body:**
```json
{
  "notes": "محتوا تأیید شد. عالی است!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "status": "approved",
    "approved_at": "2025-10-05T18:00:00Z",
    "version": {
      "id": 1,
      "version_number": 1,
      "created_at": "2025-10-05T18:00:00Z"
    }
  }
}
```

**Implementation Notes:**
- یک Version جدید ساخته می‌شود
- فقط کاربران با permission می‌توانند approve کنند

---

### 5.7. رد محتوا

**Endpoint:** `POST /api/v1/contents/{id}/reject`

**Description:** رد محتوا و تغییر وضعیت به REJECTED

**Authentication:** ✅ Yes (Bearer Token - نیاز به permission)

**Request Body:**
```json
{
  "reason": "نیاز به ویرایش بیشتر دارد. لطفا tone را رسمی‌تر کنید."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "status": "rejected",
    "rejection_reason": "نیاز به ویرایش بیشتر دارد. لطفا tone را رسمی‌تر کنید.",
    "rejected_at": "2025-10-05T18:10:00Z"
  }
}
```

---

### 5.8. لیست نسخه‌های محتوا

**Endpoint:** `GET /api/v1/contents/{id}/versions`

**Description:** دریافت تمام نسخه‌های تأییدشده یک محتوا

**Authentication:** ✅ Yes (Bearer Token)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 2,
      "version_number": 2,
      "content_snapshot": {
        "title": "بهترین محصولات پاییزی (نسخه ۲)",
        "body": "محتوای ویرایش شده...",
        "word_count": 920
      },
      "created_at": "2025-10-03T10:00:00Z",
      "created_by": {
        "id": 1,
        "full_name": "علی احمدی"
      }
    },
    {
      "id": 1,
      "version_number": 1,
      "content_snapshot": {
        "title": "بهترین محصولات پاییزی",
        "body": "محتوای اولیه...",
        "word_count": 850
      },
      "created_at": "2025-10-02T14:30:00Z",
      "created_by": {
        "id": 1,
        "full_name": "علی احمدی"
      }
    }
  ]
}
```

---

### 5.9. حذف محتوا

**Endpoint:** `DELETE /api/v1/contents/{id}`

**Description:** حذف محتوا (soft delete)

**Authentication:** ✅ Yes (Bearer Token)

**Response (204 No Content)**

**Response (403 Forbidden):**
```json
{
  "success": false,
  "error": "شما اجازه حذف این محتوا را ندارید"
}
```

---

## 6. Usage APIs

### 6.1. خلاصه مصرف

**Endpoint:** `GET /api/v1/usage/summary`

**Description:** دریافت خلاصه مصرف API

**Authentication:** ✅ Yes (Bearer Token)

**Query Parameters:**
- `scope` (optional): "user" | "workspace" | "organization" (default: "user")
- `month` (optional): YYYY-MM format (default: current month)
- `workspace_id` (optional): برای scope=workspace
- `organization_id` (optional): برای scope=organization

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "scope": "user",
    "period": "2025-10",
    "total_requests": 45,
    "total_tokens": 68500,
    "total_cost": 0.82,
    "limit": {
      "requests_limit": 1000,
      "tokens_limit": 1000000,
      "cost_limit": 50.0,
      "usage_percentage": {
        "requests": 4.5,
        "tokens": 6.85,
        "cost": 1.64
      }
    },
    "breakdown_by_model": {
      "gpt-4.1-mini": {
        "requests": 40,
        "tokens": 60000,
        "cost": 0.60
      },
      "gpt-4": {
        "requests": 5,
        "tokens": 8500,
        "cost": 0.22
      }
    },
    "daily_usage": [
      {
        "date": "2025-10-01",
        "requests": 5,
        "tokens": 7500,
        "cost": 0.09
      },
      {
        "date": "2025-10-02",
        "requests": 8,
        "tokens": 12000,
        "cost": 0.14
      }
    ]
  }
}
```

---

### 6.2. لاگ‌های مصرف

**Endpoint:** `GET /api/v1/usage/logs`

**Description:** دریافت لاگ‌های تفصیلی مصرف

**Authentication:** ✅ Yes (Bearer Token)

**Query Parameters:**
- `content_id` (optional): فیلتر بر اساس محتوا
- `start_date` (optional): YYYY-MM-DD
- `end_date` (optional): YYYY-MM-DD
- `page` (optional): شماره صفحه

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "count": 45,
    "results": [
      {
        "id": 123,
        "content": {
          "id": 2,
          "title": "معرفی محصول جدید"
        },
        "model": "gpt-4.1-mini",
        "prompt_tokens": 150,
        "completion_tokens": 850,
        "total_tokens": 1000,
        "estimated_cost": 0.012,
        "request_duration": 3.5,
        "timestamp": "2025-10-05T17:05:00Z",
        "user": {
          "id": 1,
          "full_name": "علی احمدی"
        }
      }
    ]
  }
}
```

---

### 6.3. تنظیم محدودیت مصرف

**Endpoint:** `POST /api/v1/usage/limits`

**Description:** تنظیم یا بروزرسانی محدودیت مصرف

**Authentication:** ✅ Yes (Bearer Token - نیاز به admin permission)

**Request Body:**
```json
{
  "scope": "organization",
  "scope_id": 1,
  "requests_limit": 5000,
  "tokens_limit": 5000000,
  "cost_limit": 200.0
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 5,
    "scope": "organization",
    "scope_id": 1,
    "requests_limit": 5000,
    "tokens_limit": 5000000,
    "cost_limit": 200.0,
    "period": "monthly",
    "created_at": "2025-10-05T18:30:00Z"
  }
}
```

---

## 7. Error Codes & Standard Responses

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | درخواست موفق |
| 201 | Created | ساخت منبع جدید موفق |
| 204 | No Content | حذف موفق (بدون محتوا) |
| 400 | Bad Request | خطای validation یا درخواست نامعتبر |
| 401 | Unauthorized | نیاز به authentication |
| 403 | Forbidden | کاربر دسترسی ندارد |
| 404 | Not Found | منبع یافت نشد |
| 429 | Too Many Requests | rate limit exceeded |
| 500 | Internal Server Error | خطای سرور |
| 503 | Service Unavailable | سرویس موقتاً در دسترس نیست |

### Standard Error Response

```json
{
  "success": false,
  "error": "پیام خطای کلی",
  "errors": {
    "field_name": ["validation error message"]
  },
  "code": "ERROR_CODE",
  "timestamp": "2025-10-05T18:00:00Z"
}
```

### Common Error Codes

- `INVALID_TOKEN`: Token نامعتبر
- `EXPIRED_TOKEN`: Token منقضی شده
- `PERMISSION_DENIED`: عدم دسترسی
- `RESOURCE_NOT_FOUND`: منبع یافت نشد
- `USAGE_LIMIT_EXCEEDED`: سقف مصرف تمام شده
- `INVALID_CONTENT_STATUS`: وضعیت محتوا برای این عملیات مناسب نیست
- `GENERATION_FAILED`: تولید محتوا با شکست مواجه شد
- `PII_DETECTED`: اطلاعات حساس تشخیص داده شد

---

## 8. Pagination

تمامی list APIها از pagination استفاده می‌کنند:

**Request:**
```
GET /api/v1/contents?page=2&page_size=20
```

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 150,
    "next": "http://localhost:8000/api/v1/contents?page=3&page_size=20",
    "previous": "http://localhost:8000/api/v1/contents?page=1&page_size=20",
    "results": [...]
  }
}
```

---

## 9. Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/otp/request` | 3 requests | 5 minutes |
| `/auth/otp/verify` | 5 requests | 5 minutes |
| `/contents/*/generate` | 10 requests | 1 hour |
| Other authenticated endpoints | 100 requests | 1 minute |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1696521600
```

---

## 10. Webhooks (Future)

در نسخه‌های آینده، امکان تنظیم webhook برای رویدادهای زیر فراهم خواهد شد:

- `content.generated`: تولید محتوا تکمیل شد
- `content.approved`: محتوا تأیید شد
- `usage.limit_warning`: نزدیک شدن به سقف مصرف
- `usage.limit_exceeded`: عبور از سقف مصرف

---

## نکات پیاده‌سازی

1. **Authentication Header:**
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **Content-Type:**
   ```
   Content-Type: application/json
   ```

3. **CORS:**
   - Frontend origin باید در Django CORS whitelist باشد
   - Credentials: true

4. **Timezone:**
   - تمام timestamps در UTC
   - Format: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)

5. **Validation:**
   - از DRF serializers استفاده می‌شود
   - خطاهای validation در فرمت استاندارد

6. **Transaction Management:**
   - عملیات database-heavy در transaction
   - Atomic operations برای data consistency
