'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Layout from '@/components/Layout';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import Spinner from '@/components/ui/Spinner';
import { projectApi, organizationApi, contentApi } from '@/lib/api';

interface Project {
  id: number;
  name: string;
  slug: string;
  description?: string;
  workspace: number;
  created_at: string;
  contents_count?: number;
}

interface Workspace {
  id: number;
  name: string;
  slug: string;
  organization: number;
}

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
  });
  const [formError, setFormError] = useState('');

  useEffect(() => {
    loadWorkspaces();
  }, []);

  useEffect(() => {
    if (selectedWorkspace) {
      loadProjects();
    }
  }, [selectedWorkspace]);

  const loadWorkspaces = async () => {
    try {
      const orgResponse = await organizationApi.list();
      if (orgResponse.data.success && orgResponse.data.data?.length > 0) {
        const firstOrg = orgResponse.data.data[0];
        const wsResponse = await organizationApi.getWorkspaces(firstOrg.id);
        if (wsResponse.data.success) {
          setWorkspaces(wsResponse.data.data || []);
          if (wsResponse.data.data?.length > 0) {
            setSelectedWorkspace(wsResponse.data.data[0].id);
          }
        }
      }
    } catch (error) {
      console.error('Error loading workspaces:', error);
    }
  };

  const loadProjects = async () => {
    if (!selectedWorkspace) return;
    
    setLoading(true);
    try {
      const response = await projectApi.list(selectedWorkspace);
      if (response.data.success) {
        setProjects(response.data.data || []);
      }
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWorkspace) return;

    setFormError('');
    try {
      const response = await projectApi.create({
        ...formData,
        workspace: selectedWorkspace,
      });

      if (response.data.success) {
        setShowModal(false);
        setFormData({ name: '', slug: '', description: '' });
        loadProjects();
      } else {
        setFormError(response.data.error || 'خطا در ایجاد پروژه');
      }
    } catch (error: any) {
      setFormError(error.response?.data?.error || 'خطا در ایجاد پروژه');
    }
  };

  const handleNameChange = (name: string) => {
    setFormData({
      ...formData,
      name,
      slug: name
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, ''),
    });
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">پروژه‌ها</h1>
            <p className="text-gray-600 mt-1">مدیریت پروژه‌های تولید محتوا</p>
          </div>
          <Button onClick={() => setShowModal(true)}>
            + ایجاد پروژه جدید
          </Button>
        </div>

        {/* Workspace Selector */}
        {workspaces.length > 0 && (
          <div className="flex gap-2">
            {workspaces.map((ws) => (
              <button
                key={ws.id}
                onClick={() => setSelectedWorkspace(ws.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedWorkspace === ws.id
                    ? 'bg-primary-100 text-primary-700 border-2 border-primary-300'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                {ws.name}
              </button>
            ))}
          </div>
        )}

        {/* Projects Grid */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : projects.length === 0 ? (
          <Card className="text-center py-12">
            <p className="text-gray-600 mb-4">هنوز پروژه‌ای ایجاد نشده است</p>
            <Button onClick={() => setShowModal(true)}>
              ایجاد اولین پروژه
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Card
                key={project.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/projects/${project.id}`)}
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {project.name}
                </h3>
                {project.description && (
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {project.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>📝 {project.contents_count || 0} محتوا</span>
                  <span>{new Date(project.created_at).toLocaleDateString('fa-IR')}</span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="ایجاد پروژه جدید"
        size="md"
      >
        <form onSubmit={handleCreateProject} className="space-y-4">
          <Input
            label="نام پروژه"
            value={formData.name}
            onChange={(e) => handleNameChange(e.target.value)}
            placeholder="مثال: کمپین تابستان"
            required
          />

          <Input
            label="شناسه (Slug)"
            value={formData.slug}
            onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
            placeholder="summer-campaign"
            helpText="به صورت خودکار از نام تولید می‌شود"
            dir="ltr"
            className="text-left"
          />

          <Input
            label="توضیحات (اختیاری)"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="توضیحات کوتاهی درباره پروژه"
          />

          {formError && (
            <p className="text-sm text-red-600">{formError}</p>
          )}

          <div className="flex gap-3 pt-4">
            <Button type="submit" className="flex-1">
              ایجاد پروژه
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
