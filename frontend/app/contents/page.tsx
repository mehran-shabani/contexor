'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Layout from '@/components/Layout';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import Spinner from '@/components/ui/Spinner';
import { contentApi, projectApi, promptApi, organizationApi } from '@/lib/api';

interface Content {
  id: number;
  title: string;
  status: string;
  word_count?: number;
  project: {
    id: number;
    name: string;
  };
  created_at: string;
}

interface Project {
  id: number;
  name: string;
}

interface Prompt {
  id: number;
  title: string;
  variables: string[];
}

export default function ContentsPage() {
  const router = useRouter();
  const [contents, setContents] = useState<Content[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    project: 0,
    prompt: 0,
    prompt_variables: {} as Record<string, string>,
  });
  const [formError, setFormError] = useState('');
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load contents
      const contentsResponse = await contentApi.list();
      if (contentsResponse.data.success) {
        setContents(contentsResponse.data.data?.results || []);
      }

      // Load projects
      const orgResponse = await organizationApi.list();
      if (orgResponse.data.success && orgResponse.data.data?.length > 0) {
        const firstOrg = orgResponse.data.data[0];
        const wsResponse = await organizationApi.getWorkspaces(firstOrg.id);
        if (wsResponse.data.success && wsResponse.data.data?.length > 0) {
          const projectsResponse = await projectApi.list(wsResponse.data.data[0].id);
          if (projectsResponse.data.success) {
            setProjects(projectsResponse.data.data || []);
          }
        }
      }

      // Load prompts
      const promptsResponse = await promptApi.list();
      if (promptsResponse.data.success) {
        setPrompts(promptsResponse.data.data || []);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateContent = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    try {
      const response = await contentApi.create({
        title: formData.title,
        project: formData.project,
        prompt: formData.prompt || undefined,
        prompt_variables: Object.keys(formData.prompt_variables).length > 0 
          ? formData.prompt_variables 
          : undefined,
      });

      if (response.data.success && response.data.data) {
        setShowModal(false);
        router.push(`/contents/${response.data.data.id}`);
      } else {
        setFormError(response.data.error || 'خطا در ایجاد محتوا');
      }
    } catch (error: any) {
      setFormError(error.response?.data?.error || 'خطا در ایجاد محتوا');
    }
  };

  const handlePromptChange = (promptId: number) => {
    const prompt = prompts.find(p => p.id === promptId);
    setSelectedPrompt(prompt || null);
    setFormData({
      ...formData,
      prompt: promptId,
      prompt_variables: {},
    });
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">محتواها</h1>
            <p className="text-gray-600 mt-1">لیست تمام محتواهای تولید شده</p>
          </div>
          <Button onClick={() => setShowModal(true)}>
            + ایجاد محتوای جدید
          </Button>
        </div>

        {/* Contents List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : contents.length === 0 ? (
          <Card className="text-center py-12">
            <p className="text-gray-600 mb-4">هنوز محتوایی ایجاد نشده است</p>
            <Button onClick={() => setShowModal(true)}>
              ایجاد اولین محتوا
            </Button>
          </Card>
        ) : (
          <div className="space-y-4">
            {contents.map((content) => (
              <Card
                key={content.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/contents/${content.id}`)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {content.title}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>📁 {content.project.name}</span>
                      {content.word_count && (
                        <span>📝 {content.word_count} کلمه</span>
                      )}
                      <span>{new Date(content.created_at).toLocaleDateString('fa-IR')}</span>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    content.status === 'approved' ? 'bg-green-100 text-green-800' :
                    content.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                    content.status === 'rejected' ? 'bg-red-100 text-red-800' :
                    content.status === 'review' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {content.status === 'draft' && 'پیش‌نویس'}
                    {content.status === 'in_progress' && 'در حال تولید'}
                    {content.status === 'review' && 'در بررسی'}
                    {content.status === 'approved' && 'تأیید شده'}
                    {content.status === 'rejected' && 'رد شده'}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Content Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="ایجاد محتوای جدید"
        size="lg"
      >
        <form onSubmit={handleCreateContent} className="space-y-4">
          <Input
            label="عنوان محتوا"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="عنوان محتوای خود را وارد کنید"
            required
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              پروژه
            </label>
            <select
              className="block w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={formData.project}
              onChange={(e) => setFormData({ ...formData, project: parseInt(e.target.value) })}
              required
            >
              <option value={0}>انتخاب پروژه</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              پرامپت (اختیاری)
            </label>
            <select
              className="block w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={formData.prompt}
              onChange={(e) => handlePromptChange(parseInt(e.target.value))}
            >
              <option value={0}>بدون پرامپت</option>
              {prompts.map((prompt) => (
                <option key={prompt.id} value={prompt.id}>
                  {prompt.title}
                </option>
              ))}
            </select>
          </div>

          {/* Prompt Variables */}
          {selectedPrompt && selectedPrompt.variables.length > 0 && (
            <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">متغیرهای پرامپت:</p>
              {selectedPrompt.variables.map((variable) => (
                <Input
                  key={variable}
                  label={variable}
                  value={formData.prompt_variables[variable] || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      prompt_variables: {
                        ...formData.prompt_variables,
                        [variable]: e.target.value,
                      },
                    })
                  }
                  placeholder={`مقدار ${variable} را وارد کنید`}
                />
              ))}
            </div>
          )}

          {formError && (
            <p className="text-sm text-red-600">{formError}</p>
          )}

          <div className="flex gap-3 pt-4">
            <Button type="submit" className="flex-1" disabled={formData.project === 0}>
              ایجاد محتوا
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowModal(false)}
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
