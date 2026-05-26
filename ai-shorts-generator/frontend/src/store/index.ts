import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import type {
  VideoProject,
  GenerationRequest,
  RenderJob,
  VideoEffects,
} from '@/types';

interface AppState {
  // ── Projects ──────────────────────────────
  projects: VideoProject[];
  activeProjectId: string | null;
  // ── Queue ─────────────────────────────────
  renderQueue: RenderJob[];
  // ── UI ────────────────────────────────────
  sidebarOpen: boolean;
  // ── Generation form state ─────────────────
  draftRequest: Partial<GenerationRequest>;
}

interface AppActions {
  // ── Project ───────────────────────────────
  setProjects: (projects: VideoProject[]) => void;
  addProject: (project: VideoProject) => void;
  updateProject: (id: string, partial: Partial<VideoProject>) => void;
  removeProject: (id: string) => void;
  setActiveProject: (id: string | null) => void;
  // ── Queue ─────────────────────────────────
  addRenderJob: (job: RenderJob) => void;
  updateRenderJob: (jobId: string, partial: Partial<RenderJob>) => void;
  removeRenderJob: (jobId: string) => void;
  // ── UI ────────────────────────────────────
  toggleSidebar: () => void;
  // ── Draft ─────────────────────────────────
  setDraftRequest: (partial: Partial<GenerationRequest>) => void;
  resetDraft: () => void;
  setDraftEffects: (effects: Partial<VideoEffects>) => void;
}

const DEFAULT_EFFECTS: VideoEffects = {
  auto_zoom: true,
  punch_in_out: true,
  cinematic_transitions: true,
  sound_effects: true,
  background_blur: false,
  beat_sync: true,
  motion_graphics: false,
};

const DEFAULT_DRAFT: Partial<GenerationRequest> = {
  style: 'hormozi',
  platform: 'tiktok',
  voice_model: 'openai',
  subtitle_style: 'hormozi',
  language: 'pt',
  effects: DEFAULT_EFFECTS,
};

export const useAppStore = create<AppState & AppActions>()(
  immer((set) => ({
    // ── State ─────────────────────────────────
    projects: [],
    activeProjectId: null,
    renderQueue: [],
    sidebarOpen: true,
    draftRequest: DEFAULT_DRAFT,

    // ── Project actions ───────────────────────
    setProjects: (projects) => set({ projects }),

    addProject: (project) =>
      set((s) => {
        s.projects.unshift(project);
      }),

    updateProject: (id, partial) =>
      set((s) => {
        const idx = s.projects.findIndex((p) => p.id === id);
        if (idx !== -1) Object.assign(s.projects[idx], partial);
      }),

    removeProject: (id) =>
      set((s) => {
        s.projects = s.projects.filter((p) => p.id !== id);
      }),

    setActiveProject: (id) => set({ activeProjectId: id }),

    // ── Queue actions ─────────────────────────
    addRenderJob: (job) =>
      set((s) => {
        s.renderQueue.push(job);
      }),

    updateRenderJob: (jobId, partial) =>
      set((s) => {
        const idx = s.renderQueue.findIndex((j) => j.job_id === jobId);
        if (idx !== -1) Object.assign(s.renderQueue[idx], partial);
      }),

    removeRenderJob: (jobId) =>
      set((s) => {
        s.renderQueue = s.renderQueue.filter((j) => j.job_id !== jobId);
      }),

    // ── UI actions ────────────────────────────
    toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

    // ── Draft actions ─────────────────────────
    setDraftRequest: (partial) =>
      set((s) => {
        Object.assign(s.draftRequest, partial);
      }),

    resetDraft: () => set({ draftRequest: DEFAULT_DRAFT }),

    setDraftEffects: (effects) =>
      set((s) => {
        if (s.draftRequest.effects) {
          Object.assign(s.draftRequest.effects, effects);
        }
      }),
  }))
);

// ── Selectors ────────────────────────────────
export const useActiveProject = () =>
  useAppStore((s) =>
    s.activeProjectId ? s.projects.find((p) => p.id === s.activeProjectId) : null
  );

export const useRenderingJobs = () =>
  useAppStore((s) =>
    s.renderQueue.filter(
      (j) => j.status !== 'idle' && j.status !== 'done' && j.status !== 'error'
    )
  );
