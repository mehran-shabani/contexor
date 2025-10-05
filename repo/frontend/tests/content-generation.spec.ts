import { test, expect } from '@playwright/test';

test.describe('Content Generation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'mock-access-token');
      localStorage.setItem('refresh_token', 'mock-refresh-token');
      localStorage.setItem(
        'user',
        JSON.stringify({
          id: 1,
          phone_number: '+989123456789',
          full_name: 'علی احمدی',
          is_active: true,
          date_joined: '2025-10-01T10:30:00Z',
        })
      );
    });

    // Mock API endpoints
    await page.route('**/api/v1/organizations', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: [
            {
              id: 1,
              name: 'شرکت نمونه',
              slug: 'company-demo',
              role: 'admin',
            },
          ],
        }),
      });
    });

    await page.route('**/api/v1/organizations/1/workspaces', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: [
            {
              id: 1,
              name: 'Marketing Team',
              slug: 'marketing',
              organization: 1,
            },
          ],
        }),
      });
    });

    await page.route('**/api/v1/projects?workspace=1', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: [
            {
              id: 1,
              name: 'کمپین پاییز',
              slug: 'fall-campaign',
              description: 'محتوای کمپین پاییزه',
              workspace: 1,
              contents_count: 5,
            },
          ],
        }),
      });
    });

    await page.route('**/api/v1/contents?*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            count: 1,
            results: [
              {
                id: 1,
                title: 'تست محتوا',
                status: 'draft',
                project: {
                  id: 1,
                  name: 'کمپین پاییز',
                },
                created_at: '2025-10-01T10:00:00Z',
              },
            ],
          },
        }),
      });
    });

    await page.route('**/api/v1/prompts*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: [
            {
              id: 1,
              title: 'پست وبلاگ SEO',
              category: 'blog',
              prompt_template: 'یک پست وبلاگ {word_count} کلمه‌ای درباره {topic} بنویس',
              variables: ['word_count', 'topic'],
              workspace: 1,
            },
          ],
        }),
      });
    });
  });

  test('should display content list page', async ({ page }) => {
    await page.goto('/contents');
    await expect(page.getByRole('heading', { name: /محتواها/i })).toBeVisible();
    await expect(page.getByText(/تست محتوا/i)).toBeVisible();
  });

  test('should open create content modal', async ({ page }) => {
    await page.goto('/contents');
    await page.getByRole('button', { name: /ایجاد محتوای جدید/i }).click();

    await expect(page.getByText(/ایجاد محتوای جدید/i)).toBeVisible();
    await expect(page.getByLabel(/عنوان محتوا/i)).toBeVisible();
    await expect(page.getByLabel(/پروژه/i)).toBeVisible();
  });

  test('should create new content and navigate to editor', async ({ page }) => {
    await page.route('**/api/v1/contents', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: {
              id: 2,
              title: 'محتوای جدید',
              project: 1,
              status: 'draft',
            },
          }),
        });
      }
    });

    await page.route('**/api/v1/contents/2', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            id: 2,
            title: 'محتوای جدید',
            body: null,
            status: 'draft',
            project: {
              id: 1,
              name: 'کمپین پاییز',
            },
            created_at: '2025-10-05T10:00:00Z',
            updated_at: '2025-10-05T10:00:00Z',
          },
        }),
      });
    });

    await page.goto('/contents');
    await page.getByRole('button', { name: /ایجاد محتوای جدید/i }).click();

    // Fill form
    await page.getByLabel(/عنوان محتوا/i).fill('محتوای جدید');
    await page.getByLabel(/پروژه/i).selectOption({ value: '1' });
    await page.getByRole('button', { name: /^ایجاد محتوا$/i }).click();

    // Should redirect to content editor
    await page.waitForURL('**/contents/2');
    await expect(page).toHaveURL(/\/contents\/2/);
  });

  test('should generate content', async ({ page }) => {
    await page.route('**/api/v1/contents/1', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            id: 1,
            title: 'تست محتوا',
            body: null,
            status: 'draft',
            project: {
              id: 1,
              name: 'کمپین پاییز',
            },
            created_at: '2025-10-01T10:00:00Z',
            updated_at: '2025-10-01T10:00:00Z',
          },
        }),
      });
    });

    await page.route('**/api/v1/contents/1/generate', (route) => {
      route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            task_id: 'task-123',
            status: 'in_progress',
            message: 'تولید محتوا در حال انجام است',
          },
        }),
      });
    });

    await page.goto('/contents/1');

    // Click generate button
    await page.getByRole('button', { name: /تولید محتوا/i }).click();

    // Should show generating status
    await expect(page.getByText(/در حال تولید محتوا/i)).toBeVisible();
  });
});
