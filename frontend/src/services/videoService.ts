import api from './api';
import type {
  GenerationRequest,
  VideoProject,
  AITitleSuggestions,
  AIDescriptionResult,
  GeneratedScript,
  RenderJob,
  VideoTemplate,
} from '@/types';

// ── Script ──────────────────────────────────
export const generateScript = (
  prompt: string,
  style: string,
  language = 'en'
): Promise<GeneratedScript> =>
  api.post('/ai/script', { prompt, style, language }).then((r) => r.data);

export const generateTitles = (
  script: string
): Promise<AITitleSuggestions> =>
  api.post('/ai/titles', { script }).then((r) => r.data);

export const generateDescription = (
  script: string,
  platform: string
): Promise<AIDescriptionResult> =>
  api.post('/ai/description', { script, platform }).then((r) => r.data);

// ── Projects ─────────────────────────────────
export const getProjects = (): Promise<VideoProject[]> =>
  api.get('/video/projects').then((r) => r.data);

export const createProject = (
  req: GenerationRequest
): Promise<VideoProject> =>
  api.post('/video/projects', req).then((r) => r.data);

export const getProject = (id: string): Promise<VideoProject> =>
  api.get(`/video/projects/${id}`).then((r) => r.data);

export const deleteProject = (id: string): Promise<void> =>
  api.delete(`/video/projects/${id}`).then((r) => r.data);

export const deleteAllProjects = (): Promise<{ deleted: number }> =>
  api.delete('/video/projects').then((r) => r.data);

// ── Render ────────────────────────────────────
export const startRender = (projectId: string): Promise<RenderJob> =>
  api.post(`/video/render/${projectId}`).then((r) => r.data);

export const getRenderStatus = (jobId: string): Promise<RenderJob> =>
  api.get(`/video/status/${jobId}`).then((r) => r.data);

export const cancelRender = (jobId: string): Promise<void> =>
  api.delete(`/video/render/${jobId}`).then((r) => r.data);

// ── Templates ─────────────────────────────────
export const getTemplates = (): Promise<VideoTemplate[]> =>
  api.get('/templates').then((r) => r.data);

// ── Export ────────────────────────────────────
export const downloadExport = (projectId: string): string =>
  `/api/export/download/${projectId}`;

export const getThumbnail = (projectId: string): string =>
  `/api/export/thumbnail/${projectId}`;

export const getGeneratedImageUrl = (projectId: string, filename: string): string =>
  `/api/export/images/${projectId}/${filename}`;

// ── Health ────────────────────────────────────
export const healthCheck = (): Promise<{ status: string; version: string }> =>
  api.get('/health').then((r) => r.data);
