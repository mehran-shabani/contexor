# مدل‌های دیتابیس - Contexor

## نگاه کلی

این سند تمامی مدل‌های PostgreSQL سیستم Contexor را با جزئیات کامل، شامل فیلدها، کلیدهای خارجی، ایندکس‌ها، و محدودیت‌ها شرح می‌دهد.

**Database:** PostgreSQL 15  
**ORM:** Django ORM  
**Migration System:** Django Migrations

---

## نمودار روابط (Entity Relationship Diagram)

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
│     User     │───┐   │  Organization    │───┐   │   Workspace      │
│              │   │   │                  │   │   │                  │
│  - id (PK)   │   └──>│  - id (PK)       │   └──>│  - id (PK)       │
│  - phone     │       │  - name          │       │  - name          │
│  - full_name │       │  - slug          │       │  - slug          │
│  - email     │       │  - created_at    │       │  - organization_id│
└──────┬───────┘       └─────────┬────────┘       └─────────┬────────┘
       │                         │                          │
       │                         │                          │
       │  ┌──────────────────────┴──────────────────────┐   │
       │  │     OrganizationMember                      │   │
       │  │  - id (PK)                                  │   │
       └─>│  - user_id (FK)                            │   │
          │  - organization_id (FK)                     │   │
          │  - role (admin/editor/viewer)               │   │
          └─────────────────────────────────────────────┘   │
                                                            │
       ┌────────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│     Project      │       │     Prompt       │       │     Content      │
│                  │       │                  │       │                  │
│  - id (PK)       │       │  - id (PK)       │       │  - id (PK)       │
│  - name          │       │  - title         │       │  - title         │
│  - slug          │       │  - category      │       │  - body          │
│  - workspace_id  │       │  - template      │       │  - status        │
└─────────┬────────┘       └─────────┬────────┘       │  - project_id    │
          │                          │                │  - prompt_id     │
          │                          │                │  - created_by_id │
          │                          └───────────────>└─────────┬────────┘
          │                                                     │
          └─────────────────────────────────────────────────────┘
                                                                │
                                                                │
       ┌────────────────────────────────────────────────────────┤
       │                                                        │
       ↓                                                        ↓
┌──────────────────┐                                    ┌──────────────────┐
│     Version      │                                    │    UsageLog      │
│                  │                                    │                  │
│  - id (PK)       │                                    │  - id (PK)       │
│  - content_id    │                                    │  - content_id    │
│  - version_num   │                                    │  - model         │
│  - snapshot      │                                    │  - tokens        │
└──────────────────┘                                    │  - cost          │
                                                        └──────────────────┘

┌──────────────────┐
│   UsageLimit     │
│                  │
│  - id (PK)       │
│  - scope         │
│  - scope_id      │
│  - limits        │
└──────────────────┘
```

---

## 1. User (کاربران)

### توضیحات
مدل کاربران سیستم. از AbstractBaseUser دجنگو extend می‌شود.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `phone_number` | VARCHAR(20) | UNIQUE, NOT NULL | شماره تلفن همراه (username) |
| `full_name` | VARCHAR(255) | NULL | نام و نام خانوادگی |
| `email` | VARCHAR(255) | NULL, UNIQUE | ایمیل (اختیاری) |
| `is_active` | BOOLEAN | DEFAULT TRUE | وضعیت فعال/غیرفعال |
| `is_staff` | BOOLEAN | DEFAULT FALSE | دسترسی به پنل ادمین |
| `is_superuser` | BOOLEAN | DEFAULT FALSE | دسترسی superuser |
| `date_joined` | TIMESTAMP | DEFAULT NOW() | تاریخ ثبت‌نام |
| `last_login` | TIMESTAMP | NULL | آخرین ورود |

### ایندکس‌ها

```sql
CREATE UNIQUE INDEX idx_user_phone ON users(phone_number);
CREATE INDEX idx_user_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_user_active ON users(is_active);
```

### مثال Django Model

```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_active']),
        ]
```

---

## 2. OTPCode (کدهای یکبار مصرف)

### توضیحات
ذخیره کدهای OTP برای احراز هویت. TTL: 120 ثانیه.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `phone_number` | VARCHAR(20) | NOT NULL | شماره تلفن |
| `code` | VARCHAR(6) | NOT NULL | کد 6 رقمی |
| `is_used` | BOOLEAN | DEFAULT FALSE | استفاده شده یا نه |
| `created_at` | TIMESTAMP | DEFAULT NOW() | زمان ایجاد |
| `expires_at` | TIMESTAMP | NOT NULL | زمان انقضا |

### ایندکس‌ها

```sql
CREATE INDEX idx_otp_phone_code ON otp_codes(phone_number, code) WHERE is_used = FALSE;
CREATE INDEX idx_otp_expires ON otp_codes(expires_at);
```

### Django Model

```python
class OTPCode(models.Model):
    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'otp_codes'
        indexes = [
            models.Index(fields=['phone_number', 'code']),
            models.Index(fields=['expires_at']),
        ]
```

---

## 3. Organization (سازمان)

### توضیحات
سازمان‌ها - سطح بالاترین مدیریت دسترسی.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `name` | VARCHAR(255) | NOT NULL | نام سازمان |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | نامک URL-safe |
| `description` | TEXT | NULL | توضیحات |
| `created_at` | TIMESTAMP | DEFAULT NOW() | تاریخ ایجاد |
| `updated_at` | TIMESTAMP | AUTO UPDATE | تاریخ بروزرسانی |
| `is_active` | BOOLEAN | DEFAULT TRUE | وضعیت فعال |

### ایندکس‌ها

```sql
CREATE UNIQUE INDEX idx_org_slug ON organizations(slug);
CREATE INDEX idx_org_active ON organizations(is_active) WHERE is_active = TRUE;
```

### Django Model

```python
class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'organizations'
```

---

## 4. OrganizationMember (عضویت سازمان)

### توضیحات
رابطه many-to-many بین User و Organization با role.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `user_id` | INTEGER | FK(users.id), NOT NULL | کاربر |
| `organization_id` | INTEGER | FK(organizations.id), NOT NULL | سازمان |
| `role` | VARCHAR(20) | NOT NULL | نقش کاربر |
| `joined_at` | TIMESTAMP | DEFAULT NOW() | تاریخ عضویت |

### Enums

```python
class MemberRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    EDITOR = 'editor', 'Editor'
    VIEWER = 'viewer', 'Viewer'
```

### محدودیت‌ها

```sql
ALTER TABLE organization_members 
ADD CONSTRAINT unique_user_org UNIQUE(user_id, organization_id);

ALTER TABLE organization_members 
ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE organization_members 
ADD CONSTRAINT fk_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

ALTER TABLE organization_members 
ADD CONSTRAINT check_role CHECK (role IN ('admin', 'editor', 'viewer'));
```

### ایندکس‌ها

```sql
CREATE INDEX idx_orgmember_user ON organization_members(user_id);
CREATE INDEX idx_orgmember_org ON organization_members(organization_id);
CREATE INDEX idx_orgmember_role ON organization_members(role);
```

### Django Model

```python
class OrganizationMember(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        EDITOR = 'editor', 'Editor'
        VIEWER = 'viewer', 'Viewer'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=Role.choices)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'organization_members'
        unique_together = [['user', 'organization']]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['role']),
        ]
```

---

## 5. Workspace (فضای کاری)

### توضیحات
فضاهای کاری در یک سازمان - برای تقسیم‌بندی پروژه‌ها.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `name` | VARCHAR(255) | NOT NULL | نام فضای کاری |
| `slug` | VARCHAR(100) | NOT NULL | نامک |
| `organization_id` | INTEGER | FK(organizations.id), NOT NULL | سازمان مربوطه |
| `description` | TEXT | NULL | توضیحات |
| `created_at` | TIMESTAMP | DEFAULT NOW() | تاریخ ایجاد |
| `updated_at` | TIMESTAMP | AUTO UPDATE | تاریخ بروزرسانی |
| `is_active` | BOOLEAN | DEFAULT TRUE | وضعیت فعال |

### محدودیت‌ها

```sql
ALTER TABLE workspaces 
ADD CONSTRAINT unique_org_slug UNIQUE(organization_id, slug);

ALTER TABLE workspaces 
ADD CONSTRAINT fk_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
```

### ایندکس‌ها

```sql
CREATE INDEX idx_workspace_org ON workspaces(organization_id);
CREATE INDEX idx_workspace_slug ON workspaces(slug);
CREATE INDEX idx_workspace_active ON workspaces(is_active);
```

### Django Model

```python
class Workspace(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='workspaces')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'workspaces'
        unique_together = [['organization', 'slug']]
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['is_active']),
        ]
```

---

## 6. Project (پروژه)

### توضیحات
پروژه‌های محتوایی در هر workspace.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `name` | VARCHAR(255) | NOT NULL | نام پروژه |
| `slug` | VARCHAR(100) | NOT NULL | نامک |
| `workspace_id` | INTEGER | FK(workspaces.id), NOT NULL | فضای کاری |
| `description` | TEXT | NULL | توضیحات |
| `created_by_id` | INTEGER | FK(users.id), NULL | ایجاد شده توسط |
| `created_at` | TIMESTAMP | DEFAULT NOW() | تاریخ ایجاد |
| `updated_at` | TIMESTAMP | AUTO UPDATE | تاریخ بروزرسانی |
| `is_active` | BOOLEAN | DEFAULT TRUE | وضعیت فعال |

### محدودیت‌ها

```sql
ALTER TABLE projects 
ADD CONSTRAINT unique_workspace_slug UNIQUE(workspace_id, slug);

ALTER TABLE projects 
ADD CONSTRAINT fk_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;

ALTER TABLE projects 
ADD CONSTRAINT fk_creator FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL;
```

### ایندکس‌ها

```sql
CREATE INDEX idx_project_workspace ON projects(workspace_id);
CREATE INDEX idx_project_creator ON projects(created_by_id);
CREATE INDEX idx_project_active ON projects(is_active);
```

### Django Model

```python
class Project(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='projects')
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'projects'
        unique_together = [['workspace', 'slug']]
        indexes = [
            models.Index(fields=['workspace']),
            models.Index(fields=['created_by']),
        ]
```

---

## 7. Prompt (پرامپت‌های قابل استفاده مجدد)

### توضیحات
پرامپت‌های از پیش تعریف شده برای تولید محتوا.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `title` | VARCHAR(255) | NOT NULL | عنوان پرامپت |
| `category` | VARCHAR(50) | NOT NULL | دسته‌بندی |
| `prompt_template` | TEXT | NOT NULL | متن پرامپت با متغیرها |
| `variables` | JSONB | DEFAULT '[]' | لیست متغیرهای قابل جایگزین |
| `workspace_id` | INTEGER | FK(workspaces.id), NULL | فضای کاری (null = public) |
| `is_public` | BOOLEAN | DEFAULT FALSE | عمومی یا خصوصی |
| `usage_count` | INTEGER | DEFAULT 0 | تعداد استفاده |
| `created_by_id` | INTEGER | FK(users.id), NULL | ایجاد شده توسط |
| `created_at` | TIMESTAMP | DEFAULT NOW() | تاریخ ایجاد |
| `updated_at` | TIMESTAMP | AUTO UPDATE | تاریخ بروزرسانی |

### Enums

```python
class PromptCategory(models.TextChoices):
    BLOG = 'blog', 'Blog Post'
    SOCIAL = 'social', 'Social Media'
    ECOMMERCE = 'ecommerce', 'E-commerce'
    EMAIL = 'email', 'Email Marketing'
    AD = 'ad', 'Advertisement'
    OTHER = 'other', 'Other'
```

### محدودیت‌ها

```sql
ALTER TABLE prompts 
ADD CONSTRAINT fk_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;

ALTER TABLE prompts 
ADD CONSTRAINT fk_creator FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL;
```

### ایندکس‌ها

```sql
CREATE INDEX idx_prompt_workspace ON prompts(workspace_id);
CREATE INDEX idx_prompt_category ON prompts(category);
CREATE INDEX idx_prompt_public ON prompts(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_prompt_usage ON prompts(usage_count DESC);
```

### Django Model

```python
class Prompt(models.Model):
    class Category(models.TextChoices):
        BLOG = 'blog', 'Blog Post'
        SOCIAL = 'social', 'Social Media'
        ECOMMERCE = 'ecommerce', 'E-commerce'
        EMAIL = 'email', 'Email Marketing'
        AD = 'ad', 'Advertisement'
        OTHER = 'other', 'Other'
    
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=Category.choices)
    prompt_template = models.TextField()
    variables = models.JSONField(default=list)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name='prompts')
    is_public = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_prompts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prompts'
        indexes = [
            models.Index(fields=['workspace']),
            models.Index(fields=['category']),
            models.Index(fields=['is_public']),
            models.Index(fields=['-usage_count']),
        ]
```

---

## 8. Content (محتوا)

### توضیحات
محتوای تولید شده توسط AI. دارای جریان workflow: Draft → In Progress → Review → Approved/Rejected

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `title` | VARCHAR(500) | NOT NULL | عنوان محتوا |
| `body` | TEXT | NULL | متن محتوا |
| `status` | VARCHAR(20) | NOT NULL | وضعیت محتوا |
| `project_id` | INTEGER | FK(projects.id), NOT NULL | پروژه مربوطه |
| `prompt_id` | INTEGER | FK(prompts.id), NULL | پرامپت استفاده شده |
| `prompt_variables` | JSONB | DEFAULT '{}' | مقادیر متغیرهای پرامپت |
| `word_count` | INTEGER | DEFAULT 0 | تعداد کلمات |
| `has_pii` | BOOLEAN | DEFAULT FALSE | حاوی اطلاعات حساس |
| `pii_warnings` | JSONB | DEFAULT '[]' | هشدارهای PII |
| `metadata` | JSONB | DEFAULT '{}' | متادیتا (model, tokens, etc.) |
| `created_by_id` | INTEGER | FK(users.id), NULL | ایجاد شده توسط |
| `approved_by_id` | INTEGER | FK(users.id), NULL | تأیید شده توسط |
| `created_at` | TIMESTAMP | DEFAULT NOW() | تاریخ ایجاد |
| `updated_at` | TIMESTAMP | AUTO UPDATE | تاریخ بروزرسانی |
| `approved_at` | TIMESTAMP | NULL | تاریخ تأیید |
| `rejection_reason` | TEXT | NULL | دلیل رد شدن |

### Enums

```python
class ContentStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    IN_PROGRESS = 'in_progress', 'In Progress'
    REVIEW = 'review', 'Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
```

### محدودیت‌ها

```sql
ALTER TABLE contents 
ADD CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

ALTER TABLE contents 
ADD CONSTRAINT fk_prompt FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE SET NULL;

ALTER TABLE contents 
ADD CONSTRAINT fk_creator FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE contents 
ADD CONSTRAINT fk_approver FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE contents 
ADD CONSTRAINT check_status CHECK (status IN ('draft', 'in_progress', 'review', 'approved', 'rejected'));
```

### ایندکس‌ها

```sql
CREATE INDEX idx_content_project ON contents(project_id);
CREATE INDEX idx_content_prompt ON contents(prompt_id);
CREATE INDEX idx_content_status ON contents(status);
CREATE INDEX idx_content_creator ON contents(created_by_id);
CREATE INDEX idx_content_created_at ON contents(created_at DESC);
CREATE INDEX idx_content_has_pii ON contents(has_pii) WHERE has_pii = TRUE;
CREATE INDEX idx_content_approved ON contents(approved_at DESC) WHERE status = 'approved';
```

### Django Model

```python
class Content(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        IN_PROGRESS = 'in_progress', 'In Progress'
        REVIEW = 'review', 'Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contents')
    prompt = models.ForeignKey(Prompt, on_delete=models.SET_NULL, null=True, blank=True, related_name='contents')
    prompt_variables = models.JSONField(default=dict)
    word_count = models.IntegerField(default=0)
    has_pii = models.BooleanField(default=False)
    pii_warnings = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_contents')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_contents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'contents'
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['prompt']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['has_pii']),
        ]
```

---

## 9. Version (نسخه‌های محتوا)

### توضیحات
ذخیره snapshot از هر بار تأیید محتوا.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `content_id` | INTEGER | FK(contents.id), NOT NULL | محتوای مربوطه |
| `version_number` | INTEGER | NOT NULL | شماره نسخه |
| `content_snapshot` | JSONB | NOT NULL | snapshot کامل محتوا |
| `created_by_id` | INTEGER | FK(users.id), NULL | ایجاد شده توسط |
| `created_at` | TIMESTAMP | DEFAULT NOW() | تاریخ ایجاد |

### محدودیت‌ها

```sql
ALTER TABLE versions 
ADD CONSTRAINT unique_content_version UNIQUE(content_id, version_number);

ALTER TABLE versions 
ADD CONSTRAINT fk_content FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE;

ALTER TABLE versions 
ADD CONSTRAINT fk_creator FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL;
```

### ایندکس‌ها

```sql
CREATE INDEX idx_version_content ON versions(content_id, version_number DESC);
CREATE INDEX idx_version_created_at ON versions(created_at DESC);
```

### Django Model

```python
class Version(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    content_snapshot = models.JSONField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_versions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'versions'
        unique_together = [['content', 'version_number']]
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['content', '-version_number']),
            models.Index(fields=['-created_at']),
        ]
```

---

## 10. UsageLog (لاگ مصرف API)

### توضیحات
ثبت تمامی درخواست‌های OpenAI برای tracking و billing.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `content_id` | INTEGER | FK(contents.id), NULL | محتوای مربوطه |
| `user_id` | INTEGER | FK(users.id), NULL | کاربر |
| `workspace_id` | INTEGER | FK(workspaces.id), NULL | فضای کاری |
| `organization_id` | INTEGER | FK(organizations.id), NULL | سازمان |
| `model` | VARCHAR(100) | NOT NULL | مدل OpenAI |
| `prompt_tokens` | INTEGER | NOT NULL | تعداد توکن ورودی |
| `completion_tokens` | INTEGER | NOT NULL | تعداد توکن خروجی |
| `total_tokens` | INTEGER | NOT NULL | مجموع توکن‌ها |
| `estimated_cost` | DECIMAL(10,6) | NOT NULL | هزینه تخمینی ($) |
| `request_duration` | DECIMAL(6,2) | NULL | مدت زمان درخواست (ثانیه) |
| `success` | BOOLEAN | DEFAULT TRUE | موفق/ناموفق |
| `error_message` | TEXT | NULL | پیام خطا در صورت وجود |
| `timestamp` | TIMESTAMP | DEFAULT NOW() | زمان درخواست |

### محدودیت‌ها

```sql
ALTER TABLE usage_logs 
ADD CONSTRAINT fk_content FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE SET NULL;

ALTER TABLE usage_logs 
ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE usage_logs 
ADD CONSTRAINT fk_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL;

ALTER TABLE usage_logs 
ADD CONSTRAINT fk_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL;
```

### ایندکس‌ها

```sql
CREATE INDEX idx_usage_user ON usage_logs(user_id, timestamp DESC);
CREATE INDEX idx_usage_workspace ON usage_logs(workspace_id, timestamp DESC);
CREATE INDEX idx_usage_organization ON usage_logs(organization_id, timestamp DESC);
CREATE INDEX idx_usage_timestamp ON usage_logs(timestamp DESC);
CREATE INDEX idx_usage_model ON usage_logs(model);
CREATE INDEX idx_usage_month ON usage_logs(DATE_TRUNC('month', timestamp));
```

### Django Model

```python
class UsageLog(models.Model):
    content = models.ForeignKey(Content, on_delete=models.SET_NULL, null=True, blank=True, related_name='usage_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='usage_logs')
    workspace = models.ForeignKey(Workspace, on_delete=models.SET_NULL, null=True, related_name='usage_logs')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, related_name='usage_logs')
    model = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    total_tokens = models.IntegerField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6)
    request_duration = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usage_logs'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['workspace', '-timestamp']),
            models.Index(fields=['organization', '-timestamp']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['model']),
        ]
```

---

## 11. UsageLimit (محدودیت مصرف)

### توضیحات
تعیین سقف مصرف ماهانه برای user/workspace/organization.

### فیلدها

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | شناسه یکتا |
| `scope` | VARCHAR(20) | NOT NULL | user/workspace/organization |
| `scope_id` | INTEGER | NOT NULL | شناسه موجودیت |
| `requests_limit` | INTEGER | NULL | حداکثر تعداد request |
| `tokens_limit` | INTEGER | NULL | حداکثر تعداد توکن |
| `cost_limit` | DECIMAL(10,2) | NULL | حداکثر هزینه ($) |
| `period` | VARCHAR(20) | DEFAULT 'monthly' | بازه زمانی |
| `created_at` | TIMESTAMP | DEFAULT NOW() | تاریخ ایجاد |
| `updated_at` | TIMESTAMP | AUTO UPDATE | تاریخ بروزرسانی |

### Enums

```python
class LimitScope(models.TextChoices):
    USER = 'user', 'User'
    WORKSPACE = 'workspace', 'Workspace'
    ORGANIZATION = 'organization', 'Organization'

class LimitPeriod(models.TextChoices):
    MONTHLY = 'monthly', 'Monthly'
    DAILY = 'daily', 'Daily'
```

### محدودیت‌ها

```sql
ALTER TABLE usage_limits 
ADD CONSTRAINT unique_scope_entity UNIQUE(scope, scope_id);

ALTER TABLE usage_limits 
ADD CONSTRAINT check_scope CHECK (scope IN ('user', 'workspace', 'organization'));

ALTER TABLE usage_limits 
ADD CONSTRAINT check_period CHECK (period IN ('daily', 'monthly'));
```

### ایندکس‌ها

```sql
CREATE INDEX idx_limit_scope ON usage_limits(scope, scope_id);
```

### Django Model

```python
class UsageLimit(models.Model):
    class Scope(models.TextChoices):
        USER = 'user', 'User'
        WORKSPACE = 'workspace', 'Workspace'
        ORGANIZATION = 'organization', 'Organization'
    
    class Period(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        DAILY = 'daily', 'Daily'
    
    scope = models.CharField(max_length=20, choices=Scope.choices)
    scope_id = models.IntegerField()
    requests_limit = models.IntegerField(null=True, blank=True)
    tokens_limit = models.IntegerField(null=True, blank=True)
    cost_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    period = models.CharField(max_length=20, choices=Period.choices, default=Period.MONTHLY)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'usage_limits'
        unique_together = [['scope', 'scope_id']]
        indexes = [
            models.Index(fields=['scope', 'scope_id']),
        ]
```

---

## Migration Strategy

### Initial Migrations

```python
# 0001_initial.py
# - User, OTPCode

# 0002_organizations.py
# - Organization, OrganizationMember, Workspace

# 0003_projects.py
# - Project, Prompt

# 0004_contents.py
# - Content, Version

# 0005_usage.py
# - UsageLog, UsageLimit
```

### Sample Migration Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Create custom migration for indexes
python manage.py makemigrations --empty contentmgmt
```

---

## Query Optimization Tips

### 1. استفاده از Select Related

```python
# بد
contents = Content.objects.all()
for content in contents:
    print(content.project.name)  # N+1 query problem

# خوب
contents = Content.objects.select_related('project', 'prompt', 'created_by').all()
```

### 2. استفاده از Prefetch Related

```python
# بارگذاری versions همزمان با contents
contents = Content.objects.prefetch_related('versions').filter(status='approved')
```

### 3. Query برای Dashboard Usage

```python
from django.db.models import Sum, Count
from django.utils import timezone

# مصرف ماهانه کاربر
current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
usage = UsageLog.objects.filter(
    user_id=user_id,
    timestamp__gte=current_month
).aggregate(
    total_requests=Count('id'),
    total_tokens=Sum('total_tokens'),
    total_cost=Sum('estimated_cost')
)
```

### 4. Composite Index برای جستجوی محتوا

```sql
CREATE INDEX idx_content_search ON contents(project_id, status, created_at DESC);
```

---

## Backup & Maintenance

### Backup Commands

```bash
# Full database backup
pg_dump -h localhost -U cg -d cg -F c -f backup.dump

# Restore
pg_restore -h localhost -U cg -d cg backup.dump

# Backup specific tables
pg_dump -h localhost -U cg -d cg -t contents -t versions > content_backup.sql
```

### Maintenance Tasks

```sql
-- Vacuum و آنالیز جداول
VACUUM ANALYZE contents;
VACUUM ANALYZE usage_logs;

-- پاکسازی OTPهای منقضی (در Celery Beat)
DELETE FROM otp_codes WHERE expires_at < NOW() - INTERVAL '1 day';

-- پاکسازی لاگ‌های قدیمی (نگهداری ۱ سال)
DELETE FROM usage_logs WHERE timestamp < NOW() - INTERVAL '1 year';
```

---

## Database Configuration (settings.py)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'cg'),
        'USER': os.getenv('DB_USER', 'cg'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'cg'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Connection pooling (با استفاده از pgBouncer در production)
```

---

## Notes

1. **JSONB vs JSON:**
   - استفاده از JSONB برای فیلدهایی که query می‌شوند
   - امکان ایندکس‌گذاری روی JSONB

2. **Soft Delete:**
   - به جای DELETE، از is_active=False استفاده شود
   - برای audit trail

3. **Timezone:**
   - همه timestampها در UTC
   - USE_TZ = True در Django

4. **Constraints:**
   - استفاده از database constraints برای data integrity
   - Validation در سطح database و application

5. **Performance:**
   - ایندکس‌های composite برای query patterns رایج
   - Partition کردن usage_logs در production (بر اساس ماه)
