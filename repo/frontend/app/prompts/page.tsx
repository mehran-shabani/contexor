'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
import Modal from '@/components/ui/Modal';
import Spinner from '@/components/ui/Spinner';
import { promptApi, organizationApi } from '@/lib/api';

interface Prompt {
  id: number;
  title: string;
  category: string;
  prompt_template: string;
  variables: string[];
  workspace: number;
  is_public: boolean;
  usage_count?: number;
  created_at: string;
  created_by?: {
    id: number;
    full_name: string;
  };
}

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [workspaceId, setWorkspaceId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    category: 'blog',
    prompt_template: '',
    is_public: false,
  });
  const [formError, setFormError] = useState('');

  useEffect(() => {
    loadWorkspace();
  }, []);

  useEffect(() => {
    if (workspaceId) {
      loadPrompts();
    }
  }, [workspaceId]);

  const loadWorkspace = async () => {
    try {
      const orgResponse = await organizationApi.list();
      if (orgResponse.data.success && orgResponse.data.data?.length > 0) {
        const firstOrg = orgResponse.data.data[0];
        const wsResponse = await organizationApi.getWorkspaces(firstOrg.id);
        if (wsResponse.data.success && wsResponse.data.data?.length > 0) {
          setWorkspaceId(wsResponse.data.data[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading workspace:', error);
    }
  };

  const loadPrompts = async () => {
    setLoading(true);
    try {
      const response = await promptApi.list({ workspace: workspaceId || undefined });
      if (response.data.success) {
        setPrompts(response.data.data || []);
      }
    } catch (error) {
      console.error('Error loading prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const extractVariables = (template: string): string[] => {
    const regex = /\{(\w+)\}/g;
    const matches = template.matchAll(regex);
    const vars = Array.from(matches, (m) => m[1]);
    return [...new Set(vars)]; // Remove duplicates
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceId) return;

    setFormError('');
    const variables = extractVariables(formData.prompt_template);

    try {
      if (editingPrompt) {
        // Update existing prompt
        const response = await promptApi.update(editingPrompt.id, {
          ...formData,
          variables,
        });

        if (response.data.success) {
          setShowModal(false);
          setEditingPrompt(null);
          resetForm();
          loadPrompts();
        } else {
          setFormError(response.data.error || 'خطا در بروزرسانی پرامپت');
        }
      } else {
        // Create new prompt
        const response = await promptApi.create({
          ...formData,
          variables,
          workspace: workspaceId,
        });

        if (response.data.success) {
          setShowModal(false);
          resetForm();
          loadPrompts();
        } else {
          setFormError(response.data.error || 'خطا در ایجاد پرامپت');
        }
      }
    } catch (error: any) {
      setFormError(error.response?.data?.error || 'خطا در ذخیره پرامپت');
    }
  };

  const handleEdit = (prompt: Prompt) => {
    setEditingPrompt(prompt);
    setFormData({
      title: prompt.title,
      category: prompt.category,
      prompt_template: prompt.prompt_template,
      is_public: prompt.is_public,
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('آیا از حذف این پرامپت اطمینان دارید؟')) return;

    try {
      await promptApi.delete(id);
      loadPrompts();
    } catch (error) {
      console.error('Error deleting prompt:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      category: 'blog',
      prompt_template: '',
      is_public: false,
    });
    setEditingPrompt(null);
    setFormError('');
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetForm();
  };

  const categories = [
    { value: 'blog', label: 'وبلاگ' },
    { value: 'social', label: 'شبکه‌های اجتماعی' },
    { value: 'ecommerce', label: 'فروشگاهی' },
    { value: 'marketing', label: 'بازاریابی' },
    { value: 'seo', label: 'سئو' },
    { value: 'email', label: 'ایمیل' },
    { value: 'other', label: 'سایر' },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">کتابخانه پرامپت‌ها</h1>
            <p className="text-gray-600 mt-1">مدیریت قالب‌های تولید محتوا</p>
          </div>
          <Button onClick={() => setShowModal(true)}>
            + ایجاد پرامپت جدید
          </Button>
        </div>

        {/* Prompts Grid */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : prompts.length === 0 ? (
          <Card className="text-center py-12">
            <p className="text-gray-600 mb-4">هنوز پرامپتی ایجاد نشده است</p>
            <Button onClick={() => setShowModal(true)}>
              ایجاد اولین پرامپت
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {prompts.map((prompt) => (
              <Card key={prompt.id} className="hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {prompt.title}
                    </h3>
                    <span className="text-xs px-2 py-1 bg-primary-100 text-primary-700 rounded">
                      {categories.find(c => c.value === prompt.category)?.label || prompt.category}
                    </span>
                  </div>
                  {prompt.is_public && (
                    <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                      عمومی
                    </span>
                  )}
                </div>

                <p className="text-sm text-gray-600 mb-4 line-clamp-3 bg-gray-50 p-3 rounded">
                  {prompt.prompt_template}
                </p>

                {prompt.variables.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-600 mb-2">متغیرها:</p>
                    <div className="flex flex-wrap gap-1">
                      {prompt.variables.map((variable) => (
                        <span
                          key={variable}
                          className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
                        >
                          {variable}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <span>🔥 {prompt.usage_count || 0} استفاده</span>
                  <span>{new Date(prompt.created_at).toLocaleDateString('fa-IR')}</span>
                </div>

                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleEdit(prompt)}
                    className="flex-1"
                  >
                    ✏️ ویرایش
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => handleDelete(prompt.id)}
                    className="flex-1"
                  >
                    🗑️ حذف
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Prompt Modal */}
      <Modal
        isOpen={showModal}
        onClose={handleCloseModal}
        title={editingPrompt ? 'ویرایش پرامپت' : 'ایجاد پرامپت جدید'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="عنوان پرامپت"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="مثال: پست وبلاگ SEO"
            required
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              دسته‌بندی
            </label>
            <select
              className="block w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              required
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          <Textarea
            label="متن پرامپت"
            value={formData.prompt_template}
            onChange={(e) => setFormData({ ...formData, prompt_template: e.target.value })}
            placeholder="یک پست وبلاگ {word_count} کلمه‌ای درباره {topic} بنویس..."
            helpText="از {variable_name} برای متغیرهای قابل جایگزینی استفاده کنید"
            rows={6}
            required
          />

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_public"
              checked={formData.is_public}
              onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="is_public" className="text-sm text-gray-700">
              پرامپت عمومی (قابل استفاده برای دیگران)
            </label>
          </div>

          {/* Show extracted variables */}
          {formData.prompt_template && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700 mb-2">
                متغیرهای تشخیص داده شده:
              </p>
              <div className="flex flex-wrap gap-2">
                {extractVariables(formData.prompt_template).map((variable) => (
                  <span
                    key={variable}
                    className="text-xs px-2 py-1 bg-primary-100 text-primary-700 rounded"
                  >
                    {variable}
                  </span>
                ))}
              </div>
            </div>
          )}

          {formError && (
            <p className="text-sm text-red-600">{formError}</p>
          )}

          <div className="flex gap-3 pt-4">
            <Button type="submit" className="flex-1">
              {editingPrompt ? 'بروزرسانی' : 'ایجاد'} پرامپت
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleCloseModal}
              className="flex-1"
            >
              انصراف
            </Button>
          </div>
        </form>
      </Modal>
    </Layout>
  );
}
