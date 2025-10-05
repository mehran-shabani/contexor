'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import Layout from '@/components/Layout';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Spinner from '@/components/ui/Spinner';
import MarkdownEditor from '@/components/MarkdownEditor';
import { contentApi, promptApi } from '@/lib/api';

interface Content {
  id: number;
  title: string;
  body: string | null;
  status: string;
  word_count?: number;
  has_pii?: boolean;
  pii_warnings?: string[];
  project: {
    id: number;
    name: string;
  };
  prompt?: {
    id: number;
    title: string;
    prompt_template: string;
  };
  prompt_variables?: Record<string, string>;
  metadata?: {
    model: string;
    tokens_used: number;
    generation_time: number;
  };
  created_at: string;
  updated_at: string;
}

export default function ContentEditorPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const router = useRouter();
  const contentId = parseInt(resolvedParams.id);
  
  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);

  useEffect(() => {
    loadContent();
  }, [contentId]);

  // Poll for job status if generating
  useEffect(() => {
    if (generating && taskId) {
      const interval = setInterval(async () => {
        await loadContent();
      }, 3000); // Poll every 3 seconds

      return () => clearInterval(interval);
    }
  }, [generating, taskId]);

  const loadContent = async () => {
    try {
      const response = await contentApi.get(contentId);
      if (response.data.success && response.data.data) {
        const contentData = response.data.data;
        setContent(contentData);
        setTitle(contentData.title);
        setBody(contentData.body || '');

        // Check if generation is complete
        if (contentData.status === 'draft' && contentData.body) {
          setGenerating(false);
          setTaskId(null);
        } else if (contentData.status === 'in_progress') {
          setGenerating(true);
        }
      }
    } catch (error) {
      console.error('Error loading content:', error);
      setError('خطا در بارگذاری محتوا');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');

    try {
      const response = await contentApi.update(contentId, {
        title,
        body,
      });

      if (response.data.success) {
        await loadContent();
      } else {
        setError(response.data.error || 'خطا در ذخیره محتوا');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در ذخیره محتوا');
    } finally {
      setSaving(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');

    try {
      const response = await contentApi.generate(contentId, {
        model: 'gpt-4.1-mini',
        temperature: 0.7,
        max_tokens: 2000,
      });

      if (response.data.success && response.data.data) {
        setTaskId(response.data.data.task_id);
      } else {
        setError(response.data.error || 'خطا در تولید محتوا');
        setGenerating(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در تولید محتوا');
      setGenerating(false);
    }
  };

  const handleApprove = async () => {
    try {
      const response = await contentApi.approve(contentId, 'محتوا تأیید شد');
      if (response.data.success) {
        await loadContent();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در تأیید محتوا');
    }
  };

  const handleReject = async () => {
    const reason = prompt('دلیل رد محتوا را وارد کنید:');
    if (!reason) return;

    try {
      const response = await contentApi.reject(contentId, reason);
      if (response.data.success) {
        await loadContent();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در رد محتوا');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </Layout>
    );
  }

  if (!content) {
    return (
      <Layout>
        <Card className="text-center py-12">
          <p className="text-red-600">محتوا یافت نشد</p>
        </Card>
      </Layout>
    );
  }

  const canEdit = content.status === 'draft' || content.status === 'review';
  const canGenerate = content.status === 'draft' && !content.body;
  const canApprove = content.status === 'review' || (content.status === 'draft' && content.body);

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.back()}
              className="mb-2"
            >
              ← بازگشت
            </Button>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="text-2xl font-bold border-0 px-0 focus:ring-0"
              placeholder="عنوان محتوا"
              readOnly={!canEdit}
            />
          </div>

          <div className="flex gap-2">
            {canGenerate && (
              <Button onClick={handleGenerate} isLoading={generating}>
                ⚡ تولید محتوا
              </Button>
            )}
            {canEdit && content.body && (
              <Button onClick={handleSave} isLoading={saving}>
                💾 ذخیره
              </Button>
            )}
            {canApprove && (
              <>
                <Button onClick={handleApprove} variant="primary">
                  ✓ تأیید
                </Button>
                <Button onClick={handleReject} variant="danger">
                  ✗ رد
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Status & Info */}
        <Card>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">وضعیت:</span>
              <span className={`mr-2 px-2 py-1 rounded text-xs font-medium ${
                content.status === 'approved' ? 'bg-green-100 text-green-800' :
                content.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                content.status === 'rejected' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {content.status === 'draft' && 'پیش‌نویس'}
                {content.status === 'in_progress' && 'در حال تولید'}
                {content.status === 'review' && 'در بررسی'}
                {content.status === 'approved' && 'تأیید شده'}
                {content.status === 'rejected' && 'رد شده'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">پروژه:</span>
              <span className="mr-2 font-medium">{content.project.name}</span>
            </div>
            {content.word_count && (
              <div>
                <span className="text-gray-600">تعداد کلمات:</span>
                <span className="mr-2 font-medium">{content.word_count}</span>
              </div>
            )}
            {content.metadata && (
              <div>
                <span className="text-gray-600">توکن‌های مصرفی:</span>
                <span className="mr-2 font-medium">{content.metadata.tokens_used}</span>
              </div>
            )}
          </div>

          {content.has_pii && content.pii_warnings && content.pii_warnings.length > 0 && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800 font-medium mb-2">⚠️ هشدار: اطلاعات حساس تشخیص داده شد</p>
              <ul className="text-sm text-yellow-700 list-disc mr-5">
                {content.pii_warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </Card>

        {/* Generating Status */}
        {generating && (
          <Card className="text-center py-8">
            <Spinner size="lg" className="mb-4" />
            <p className="text-gray-700 font-medium">در حال تولید محتوا...</p>
            <p className="text-sm text-gray-600 mt-2">این فرآیند ممکن است چند دقیقه طول بکشد.</p>
          </Card>
        )}

        {/* Editor */}
        {!generating && (
          <Card>
            <MarkdownEditor
              value={body}
              onChange={setBody}
              onSave={canEdit ? handleSave : undefined}
              readOnly={!canEdit}
            />
          </Card>
        )}

        {/* Error */}
        {error && (
          <Card className="bg-red-50 border-red-200">
            <p className="text-red-600">{error}</p>
          </Card>
        )}

        {/* Prompt Info */}
        {content.prompt && (
          <Card>
            <h3 className="font-semibold mb-2">پرامپت استفاده شده:</h3>
            <p className="text-sm text-gray-700 mb-2">{content.prompt.title}</p>
            <p className="text-xs text-gray-600 bg-gray-50 p-3 rounded">
              {content.prompt.prompt_template}
            </p>
            {content.prompt_variables && Object.keys(content.prompt_variables).length > 0 && (
              <div className="mt-3">
                <p className="text-sm font-medium mb-2">متغیرها:</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(content.prompt_variables).map(([key, value]) => (
                    <div key={key} className="bg-gray-50 p-2 rounded">
                      <span className="text-gray-600">{key}:</span>
                      <span className="mr-2 font-medium">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </Layout>
  );
}
