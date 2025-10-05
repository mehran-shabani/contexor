# Contexor Frontend - Next.js 15 App Router

سیستم مدیریت محتوای هوشمند با Next.js 15 و App Router

## ویژگی‌ها

### 🔐 احراز هویت
- ورود دو مرحله‌ای با OTP
- مدیریت امن توکن‌ها (Access & Refresh)
- رفرش خودکار توکن
- ذخیره‌سازی امن در localStorage

### 📝 مدیریت محتوا
- ویرایشگر Markdown با پشتیبانی RTL
- پیش‌نمایش زنده
- پشتیبانی از H2/H3، Bold، Italic
- شمارش کلمات خودکار
- تولید محتوا با AI (OpenAI)
- وضعیت‌های مختلف: Draft, In Progress, Review, Approved, Rejected
- نسخه‌بندی محتوا
- تشخیص اطلاعات حساس (PII)

### ⚡ مدیریت پرامپت‌ها
- CRUD کامل
- دسته‌بندی پرامپت‌ها
- متغیرهای پارامتریک (tone/audience/length/keywords)
- پرامپت‌های عمومی و خصوصی
- تشخیص خودکار متغیرها از متن پرامپت

### 📊 گزارش مصرف
- خلاصه مصرف ماهانه
- نمودار مصرف روزانه
- تفکیک بر اساس مدل AI
- نمایش محدودیت‌ها و درصد استفاده
- آمار درخواست‌ها، توکن‌ها، و هزینه

### 🎨 UI/UX
- طراحی RTL (راست به چپ)
- تایپوگرافی فارسی مناسب
- Tailwind CSS
- کامپوننت‌های قابل استفاده مجدد
- پاسخگویی کامل (Responsive)
- حالت تاریک (Dark Mode Ready)

## نصب و راه‌اندازی

### پیش‌نیازها
- Node.js 18+ 
- npm یا yarn
- Backend آماده و در حال اجرا

### مراحل نصب

1. نصب وابستگی‌ها:
```bash
cd frontend
npm install
```

2. ایجاد فایل `.env.local`:
```bash
cp .env.local.example .env.local
```

3. تنظیم متغیرهای محیطی:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api/v1
```

4. اجرای در محیط توسعه:
```bash
npm run dev
```

برنامه در آدرس `http://localhost:3000` در دسترس خواهد بود.

## اسکریپت‌های موجود

```bash
# اجرای در محیط توسعه
npm run dev

# ساخت برای محیط تولید
npm run build

# اجرای محیط تولید
npm start

# بررسی کد (Linting)
npm run lint

# اجرای تست‌ها
npm test

# اجرای تست‌ها با UI
npm run test:ui
```

## ساختار پروژه

```
frontend/
├── app/                      # Next.js 15 App Router
│   ├── api/                  # API Routes
│   │   └── backend/          # Proxy به Backend
│   ├── contents/             # صفحات محتوا
│   │   └── [id]/            # ویرایشگر محتوا
│   ├── login/               # صفحه ورود
│   ├── projects/            # صفحات پروژه
│   ├── prompts/             # مدیریت پرامپت‌ها
│   ├── usage/               # گزارش مصرف
│   ├── layout.tsx           # Layout اصلی
│   └── page.tsx             # صفحه اصلی
├── components/              # کامپوننت‌های قابل استفاده مجدد
│   ├── ui/                  # کامپوننت‌های UI
│   ├── Layout.tsx           # Layout داخلی
│   ├── MarkdownEditor.tsx   # ویرایشگر Markdown
│   └── SimpleChart.tsx      # نمودار ساده
├── lib/                     # توابع کمکی
│   ├── api.ts              # API Client & Helpers
│   └── auth.ts             # مدیریت احراز هویت
├── tests/                   # تست‌های Playwright
│   ├── login.spec.ts
│   └── content-generation.spec.ts
├── public/                  # فایل‌های استاتیک
├── next.config.js          # تنظیمات Next.js
├── tailwind.config.js      # تنظیمات Tailwind
└── tsconfig.json           # تنظیمات TypeScript
```

## مسیرهای اصلی

- `/login` - صفحه ورود با OTP
- `/projects` - لیست پروژه‌ها
- `/contents` - لیست محتواها
- `/contents/[id]` - ویرایشگر محتوا
- `/prompts` - مدیریت پرامپت‌ها
- `/usage` - گزارش مصرف

## API Integration

تمامی درخواست‌ها از طریق `/lib/api.ts` مدیریت می‌شوند:

```typescript
import { contentApi } from '@/lib/api';

// دریافت لیست محتواها
const response = await contentApi.list();

// ایجاد محتوای جدید
const newContent = await contentApi.create({
  title: 'عنوان',
  project: 1,
});

// تولید محتوا با AI
await contentApi.generate(contentId);
```

## احراز هویت

مدیریت توکن‌ها از طریق `/lib/auth.ts`:

```typescript
import { authStorage } from '@/lib/auth';

// ذخیره توکن‌ها
authStorage.setTokens({ access, refresh });

// دریافت توکن
const token = authStorage.getAccessToken();

// بررسی وضعیت ورود
if (authStorage.isAuthenticated()) {
  // ...
}
```

## تست‌ها

### اجرای تست‌ها

```bash
# نصب Playwright browsers (اولین بار)
npx playwright install

# اجرای تمام تست‌ها
npm test

# اجرای با UI Mode
npm run test:ui

# اجرای یک فایل خاص
npx playwright test tests/login.spec.ts
```

### تست‌های موجود

1. **Login Flow** (`tests/login.spec.ts`)
   - نمایش صفحه ورود
   - اعتبارسنجی شماره تلفن
   - ارسال OTP
   - تأیید OTP و ورود

2. **Content Generation** (`tests/content-generation.spec.ts`)
   - نمایش لیست محتواها
   - ایجاد محتوای جدید
   - تولید محتوا با AI

## کامپوننت‌های قابل استفاده مجدد

### Button
```tsx
<Button variant="primary" size="md" onClick={handleClick}>
  کلیک کنید
</Button>
```

### Input
```tsx
<Input
  label="نام"
  value={value}
  onChange={(e) => setValue(e.target.value)}
  error={error}
/>
```

### Card
```tsx
<Card padding="md">
  محتوای کارت
</Card>
```

### Modal
```tsx
<Modal isOpen={open} onClose={() => setOpen(false)} title="عنوان">
  محتوای مودال
</Modal>
```

### MarkdownEditor
```tsx
<MarkdownEditor
  value={markdown}
  onChange={setMarkdown}
  onSave={handleSave}
/>
```

## Styling

پروژه از Tailwind CSS استفاده می‌کند:

```tsx
<div className="flex items-center justify-between p-4 bg-white rounded-lg">
  {/* محتوا */}
</div>
```

## RTL Support

تمامی صفحات به صورت پیش‌فرض RTL هستند:

```css
/* در globals.css */
body {
  direction: rtl;
}

.rtl {
  direction: rtl;
  text-align: right;
}

.ltr {
  direction: ltr;
  text-align: left;
}
```

## معیارهای پذیرش

✅ کاربر با OTP وارد می‌شود  
✅ پروژه می‌سازد  
✅ محتوا ایجاد می‌کند  
✅ دکمه Generate را می‌زند  
✅ نسخه‌ی جدید را با H2/H3 می‌بیند  
✅ صفحه‌ی Usage نمودار مصرف ماهانه را نشان می‌دهد  
✅ مدیریت Promptها کار می‌کند  

## ملاحظات امنیتی

- توکن‌ها در localStorage ذخیره می‌شوند
- رفرش خودکار access token
- Authorization header در تمام درخواست‌ها
- Validation سمت کلاینت برای تمام فرم‌ها
- CORS configuration در Backend

## Deployment

### Build برای Production

```bash
npm run build
npm start
```

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

## مشکلات رایج

### Backend در دسترس نیست
- اطمینان حاصل کنید Backend در حال اجرا است
- `NEXT_PUBLIC_BACKEND_URL` را بررسی کنید

### توکن منقضی شده
- سیستم به صورت خودکار توکن را رفرش می‌کند
- در صورت عدم موفقیت، کاربر به صفحه login هدایت می‌شود

### مشکل در نمایش فونت فارسی
- فونت Iran Sans به صورت خودکار بارگذاری می‌شود
- در صورت نیاز، فایل فونت را به `/public/fonts` اضافه کنید

## مشارکت

برای مشارکت در توسعه:

1. Fork کنید
2. Branch جدید بسازید (`git checkout -b feature/AmazingFeature`)
3. تغییرات را commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request باز کنید

## لایسنس

این پروژه تحت لایسنس MIT است.

## پشتیبانی

برای سوالات و مشکلات:
- Issue در GitHub باز کنید
- به تیم توسعه پیام دهید

---

**نکته**: این پروژه با Next.js 15 و App Router ساخته شده است. برای اطلاعات بیشتر به [مستندات Next.js](https://nextjs.org/docs) مراجعه کنید.
