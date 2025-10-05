import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { authStorage } from './auth';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000/api/v1';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  errors?: Record<string, string[]>;
  code?: string;
  timestamp?: string;
}

// Create axios instance
const api = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = authStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse>) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // If 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = authStorage.getRefreshToken();
        if (refreshToken) {
          const response = await axios.post<ApiResponse<{ access: string }>>(
            `${BACKEND_URL}/auth/token/refresh`,
            { refresh: refreshToken }
          );

          if (response.data.success && response.data.data?.access) {
            authStorage.setTokens({
              access: response.data.data.access,
              refresh: refreshToken,
            });

            // Retry original request with new token
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${response.data.data.access}`;
            }
            return api(originalRequest);
          }
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        authStorage.clear();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// API Helper Functions
export const authApi = {
  requestOtp: (phone_number: string) =>
    api.post<ApiResponse>('/auth/otp/request', { phone_number }),

  verifyOtp: (phone_number: string, code: string) =>
    api.post<ApiResponse<{ access: string; refresh: string; user: any }>>('/auth/otp/verify', {
      phone_number,
      code,
    }),

  refreshToken: (refresh: string) =>
    api.post<ApiResponse<{ access: string }>>('/auth/token/refresh', { refresh }),

  logout: (refresh: string) =>
    api.post<ApiResponse>('/auth/logout', { refresh }),
};

export const userApi = {
  getProfile: () =>
    api.get<ApiResponse>('/users/me'),

  updateProfile: (data: { full_name?: string; email?: string }) =>
    api.patch<ApiResponse>('/users/me', data),
};

export const organizationApi = {
  list: () =>
    api.get<ApiResponse>('/organizations'),

  create: (data: { name: string; slug: string }) =>
    api.post<ApiResponse>('/organizations', data),

  getWorkspaces: (orgId: number) =>
    api.get<ApiResponse>(`/organizations/${orgId}/workspaces`),

  createWorkspace: (orgId: number, data: { name: string; slug: string }) =>
    api.post<ApiResponse>(`/organizations/${orgId}/workspaces`, data),
};

export const projectApi = {
  list: (workspaceId: number) =>
    api.get<ApiResponse>('/projects', { params: { workspace: workspaceId } }),

  create: (data: { name: string; slug: string; description?: string; workspace: number }) =>
    api.post<ApiResponse>('/projects', data),

  get: (id: number) =>
    api.get<ApiResponse>(`/projects/${id}`),

  update: (id: number, data: Partial<{ name: string; description: string }>) =>
    api.patch<ApiResponse>(`/projects/${id}`, data),

  delete: (id: number) =>
    api.delete<ApiResponse>(`/projects/${id}`),
};

export const contentApi = {
  list: (params?: { project?: number; status?: string; search?: string; page?: number }) =>
    api.get<ApiResponse>('/contents', { params }),

  create: (data: {
    title: string;
    project: number;
    prompt?: number;
    prompt_variables?: Record<string, string>;
  }) =>
    api.post<ApiResponse>('/contents', data),

  get: (id: number) =>
    api.get<ApiResponse>(`/contents/${id}`),

  update: (id: number, data: Partial<{ title: string; body: string }>) =>
    api.patch<ApiResponse>(`/contents/${id}`, data),

  delete: (id: number) =>
    api.delete<ApiResponse>(`/contents/${id}`),

  generate: (id: number, options?: { model?: string; temperature?: number; max_tokens?: number }) =>
    api.post<ApiResponse<{ task_id: string; status: string }>>(`/contents/${id}/generate`, options),

  approve: (id: number, notes?: string) =>
    api.post<ApiResponse>(`/contents/${id}/approve`, { notes }),

  reject: (id: number, reason: string) =>
    api.post<ApiResponse>(`/contents/${id}/reject`, { reason }),

  getVersions: (id: number) =>
    api.get<ApiResponse>(`/contents/${id}/versions`),
};

export const promptApi = {
  list: (params?: { workspace?: number; category?: string; search?: string }) =>
    api.get<ApiResponse>('/prompts', { params }),

  get: (id: number) =>
    api.get<ApiResponse>(`/prompts/${id}`),

  create: (data: {
    title: string;
    category: string;
    prompt_template: string;
    variables: string[];
    workspace: number;
    is_public?: boolean;
  }) =>
    api.post<ApiResponse>('/prompts', data),

  update: (id: number, data: Partial<{
    title: string;
    category: string;
    prompt_template: string;
    variables: string[];
    is_public: boolean;
  }>) =>
    api.patch<ApiResponse>(`/prompts/${id}`, data),

  delete: (id: number) =>
    api.delete<ApiResponse>(`/prompts/${id}`),
};

export const usageApi = {
  getSummary: (params?: {
    scope?: 'user' | 'workspace' | 'organization';
    month?: string;
    workspace_id?: number;
    organization_id?: number;
  }) =>
    api.get<ApiResponse>('/usage/summary', { params }),

  getLogs: (params?: {
    content_id?: number;
    start_date?: string;
    end_date?: string;
    page?: number;
  }) =>
    api.get<ApiResponse>('/usage/logs', { params }),

  setLimits: (data: {
    scope: 'user' | 'workspace' | 'organization';
    scope_id: number;
    requests_limit?: number;
    tokens_limit?: number;
    cost_limit?: number;
  }) =>
    api.post<ApiResponse>('/usage/limits', data),
};
