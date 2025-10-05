import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login page with phone input', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Contexor/i })).toBeVisible();
    await expect(page.getByLabel(/شماره موبایل/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /ارسال کد تأیید/i })).toBeVisible();
  });

  test('should show validation error for invalid phone number', async ({ page }) => {
    const phoneInput = page.getByLabel(/شماره موبایل/i);
    const submitButton = page.getByRole('button', { name: /ارسال کد تأیید/i });

    await phoneInput.fill('123');
    await submitButton.click();

    // Check if error is displayed (this depends on your validation implementation)
    await expect(page.getByText(/نامعتبر/i)).toBeVisible();
  });

  test('should proceed to OTP verification step', async ({ page }) => {
    // Mock the API response
    await page.route('**/api/v1/auth/otp/request', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            phone_number: '+989123456789',
            ttl: 120,
            message: 'کد تأیید به شماره شما ارسال شد',
          },
        }),
      });
    });

    const phoneInput = page.getByLabel(/شماره موبایل/i);
    const submitButton = page.getByRole('button', { name: /ارسال کد تأیید/i });

    await phoneInput.fill('09123456789');
    await submitButton.click();

    // Should show OTP input
    await expect(page.getByLabel(/کد تأیید/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /تأیید و ورود/i })).toBeVisible();
  });

  test('should allow going back to phone input', async ({ page }) => {
    // First, go to OTP step
    await page.route('**/api/v1/auth/otp/request', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            phone_number: '+989123456789',
            ttl: 120,
            message: 'کد تأیید به شماره شما ارسال شد',
          },
        }),
      });
    });

    await page.getByLabel(/شماره موبایل/i).fill('09123456789');
    await page.getByRole('button', { name: /ارسال کد تأیید/i }).click();

    // Click back button
    await page.getByRole('button', { name: /بازگشت/i }).click();

    // Should be back to phone input
    await expect(page.getByLabel(/شماره موبایل/i)).toBeVisible();
  });

  test('should successfully login with valid OTP', async ({ page }) => {
    // Mock OTP request
    await page.route('**/api/v1/auth/otp/request', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            phone_number: '+989123456789',
            ttl: 120,
            message: 'کد تأیید به شماره شما ارسال شد',
          },
        }),
      });
    });

    // Mock OTP verify
    await page.route('**/api/v1/auth/otp/verify', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            access: 'mock-access-token',
            refresh: 'mock-refresh-token',
            user: {
              id: 1,
              phone_number: '+989123456789',
              full_name: 'علی احمدی',
              is_active: true,
              date_joined: '2025-10-01T10:30:00Z',
            },
          },
        }),
      });
    });

    // Enter phone number
    await page.getByLabel(/شماره موبایل/i).fill('09123456789');
    await page.getByRole('button', { name: /ارسال کد تأیید/i }).click();

    // Enter OTP
    await page.getByLabel(/کد تأیید/i).fill('123456');
    await page.getByRole('button', { name: /تأیید و ورود/i }).click();

    // Should redirect to projects page
    await page.waitForURL('**/projects');
    await expect(page).toHaveURL(/\/projects/);
  });
});
