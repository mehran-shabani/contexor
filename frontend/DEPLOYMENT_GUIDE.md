# راهنمای استقرار و راه‌اندازی Frontend

## 🚀 راه‌اندازی سریع

### پیش‌نیازها
```bash
Node.js >= 18
npm >= 9
Backend Django در حال اجرا
```

### نصب و راه‌اندازی

```bash
# 1. نصب وابستگی‌ها
cd /workspace/frontend
npm install

# 2. ایجاد فایل محیطی
cp .env.local.example .env.local

# 3. ویرایش .env.local
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api/v1

# 4. اجرای در محیط توسعه
npm run dev

# Frontend در آدرس http://localhost:3000 اجرا می‌شود
```

### نصب Playwright (برای تست‌ها)
```bash
npx playwright install
```

---

## 📦 Build برای Production

```bash
# 1. Build
npm run build

# 2. اجرا
npm start

# یا با PM2
pm2 start npm --name "contexor-frontend" -- start
```

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t contexor-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_BACKEND_URL=http://backend:8000/api/v1 \
  contexor-frontend
```

---

## ✅ تست کردن

```bash
# اجرای تمام تست‌ها
npm test

# اجرای با UI
npm run test:ui

# اجرای یک فایل خاص
npx playwright test tests/login.spec.ts

# اجرای در حالت headed (با مرورگر)
npx playwright test --headed
```

---

## 🔍 بررسی وضعیت

### چک‌لیست قبل از استفاده:

1. **Backend در حال اجرا است؟**
   ```bash
   curl http://localhost:8000/api/v1/
   ```

2. **Environment variables تنظیم شده؟**
   ```bash
   cat .env.local
   ```

3. **Dependencies نصب شده؟**
   ```bash
   npm list
   ```

4. **Build موفق است؟**
   ```bash
   npm run build
   ```

---

## 🎯 مسیرهای کلیدی

| مسیر | توضیحات |
|------|---------|
| `/login` | صفحه ورود با OTP |
| `/projects` | لیست و مدیریت پروژه‌ها |
| `/contents` | لیست محتواها |
| `/contents/[id]` | ویرایشگر محتوا |
| `/prompts` | مدیریت پرامپت‌ها |
| `/usage` | گزارش مصرف |

---

## 🔧 تنظیمات پیشنهادی Production

### Environment Variables
```env
NEXT_PUBLIC_BACKEND_URL=https://api.contexor.com/v1
NODE_ENV=production
```

### Performance
- Enable Redis caching در Backend
- استفاده از CDN برای static assets
- Gzip compression
- Image optimization

### Security
- HTTPS only
- Secure headers
- CORS configuration
- Rate limiting در Backend

---

## 📊 Monitoring

### Logs
```bash
# Development
npm run dev

# Production (با PM2)
pm2 logs contexor-frontend

# Docker
docker logs -f container_name
```

### Health Check
```bash
curl http://localhost:3000/
```

---

## 🐛 عیب‌یابی

### مشکل: Backend در دسترس نیست
```bash
# بررسی Backend
curl http://localhost:8000/api/v1/

# بررسی .env.local
echo $NEXT_PUBLIC_BACKEND_URL
```

### مشکل: Build شکست می‌خورد
```bash
# پاک کردن cache
rm -rf .next
rm -rf node_modules
npm install
npm run build
```

### مشکل: تست‌ها fail می‌شوند
```bash
# بررسی Backend در حال اجراست
# بررسی port 3000 آزاد است
lsof -i :3000

# نصب مجدد Playwright
npx playwright install
```

---

## 📝 Checklist استقرار

- [ ] Backend اجرا و در دسترس است
- [ ] Environment variables تنظیم شده
- [ ] Dependencies نصب شده (`npm install`)
- [ ] Build موفق است (`npm run build`)
- [ ] تست‌ها pass می‌شوند (`npm test`)
- [ ] Frontend روی port صحیح اجرا می‌شود
- [ ] Login با OTP کار می‌کند
- [ ] ایجاد پروژه کار می‌کند
- [ ] تولید محتوا کار می‌کند
- [ ] گزارش مصرف نمایش داده می‌شود

---

## 🎉 پس از استقرار

### تست Flow کامل:

1. **ورود**
   - برو به `/login`
   - شماره موبایل: `09123456789`
   - کد OTP را وارد کن
   - باید redirect به `/projects` شوی

2. **ایجاد پروژه**
   - کلیک روی "ایجاد پروژه جدید"
   - نام پروژه را وارد کن
   - پروژه ساخته شود

3. **ایجاد محتوا**
   - برو به `/contents`
   - کلیک روی "ایجاد محتوای جدید"
   - پروژه و پرامپت را انتخاب کن
   - محتوا ساخته شود

4. **تولید محتوا**
   - وارد ویرایشگر محتوا شو
   - کلیک روی "تولید محتوا"
   - منتظر بمان تا تولید کامل شود
   - محتوا با H2/H3 نمایش داده شود

5. **بررسی گزارش مصرف**
   - برو به `/usage`
   - نمودار مصرف را ببین
   - آمار به روز باشد

---

## 📞 پشتیبانی

اگر مشکلی وجود داشت:
1. Logs را بررسی کنید
2. به README.md مراجعه کنید
3. به IMPLEMENTATION_SUMMARY.md مراجعه کنید
4. Issue باز کنید

---

**آخرین بروزرسانی**: 2025-10-05  
**نسخه**: 1.0.0  
**وضعیت**: ✅ آماده برای استفاده
