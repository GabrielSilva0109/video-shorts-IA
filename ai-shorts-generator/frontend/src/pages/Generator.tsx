import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Wand2, FileText, Play } from 'lucide-react';
import GeneratorForm from '@components/GeneratorForm/GeneratorForm';
import VideoPreview from '@components/VideoPreview/VideoPreview';
import { createProject, startRender } from '@/services/videoService';
import { useAppStore } from '@/store';

export default function Generator() {
  const { draftRequest, addProject, addRenderJob, updateProject, projects, activeProjectId, setActiveProject } = useAppStore();
  // Track only the ID — derive the project from the store so it stays reactive
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const [step, setStep] = useState<'form' | 'preview'>('form');

  // currentProject is always fresh from the store (auto-updates on polling)
  const currentProject = currentProjectId
    ? (projects.find((p) => p.id === currentProjectId) ?? null)
    : null;

  // Restore project if navigated from Home
  useEffect(() => {
    if (activeProjectId && !currentProjectId) {
      setCurrentProjectId(activeProjectId);
      setStep('preview');
      setActiveProject(null);
    }
  }, [activeProjectId, currentProjectId, setActiveProject]);

  // 1. Create project (generates script)
  const createMutation = useMutation({
    mutationFn: () =>
      createProject({
        prompt: draftRequest.prompt ?? '',
        style: draftRequest.style ?? 'hormozi',
        platform: draftRequest.platform ?? 'tiktok',
        voice_model: draftRequest.voice_model ?? 'openai',
        subtitle_style: draftRequest.subtitle_style ?? 'hormozi',
        background_music: draftRequest.background_music,
        language: draftRequest.language ?? 'en',
        effects: draftRequest.effects!,
      }),
    onSuccess: (project) => {
      addProject(project);
      setCurrentProjectId(project.id);
      setStep('preview');
      toast.success('Project created — ready to render!');
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });

  // 2. Start render
  const renderMutation = useMutation({
    mutationFn: () => startRender(currentProject!.id),
    onSuccess: (job) => {
      addRenderJob(job);
      updateProject(currentProject!.id, { status: 'queued', progress: 0 });
      toast.success('Render started!');
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });

  return (
    <div className="max-w-5xl mx-auto grid grid-cols-5 gap-6">
      {/* ── Left panel ──────────────────────── */}
      <div className="col-span-3 flex flex-col gap-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-display font-bold">
            {step === 'form' ? (
              <>
                <Wand2 className="inline w-6 h-6 text-neon-purple mr-2" />
                Create Video
              </>
            ) : (
              <>
                <FileText className="inline w-6 h-6 text-neon-blue mr-2" />
                Review & Render
              </>
            )}
          </h1>
          {step === 'preview' && (
            <button
              className="btn-ghost text-xs ml-auto"
              onClick={() => setStep('form')}
            >
              ← Back
            </button>
          )}
        </div>

        <div className="card p-6">
          {step === 'form' ? (
            <GeneratorForm
              onSubmit={() => createMutation.mutate()}
              loading={createMutation.isPending}
            />
          ) : currentProject?.script ? (
            <ScriptReview
              script={currentProject.script.full_text}
              hook={currentProject.script.hook}
              duration={currentProject.script.estimated_duration}
              onRender={() => renderMutation.mutate()}
              loading={renderMutation.isPending}
            />
          ) : null}
        </div>
      </div>

      {/* ── Right panel — preview ────────────── */}
      <div className="col-span-2 flex flex-col gap-4">
        <h2 className="text-lg font-display font-semibold">Preview</h2>
        <div className="card p-4">
          {currentProject ? (
            <VideoPreview
              projectId={currentProject.id}
              videoUrl={
                currentProject.status === 'done'
                  ? `/api/export/download/${currentProject.id}`
                  : undefined
              }
            />
          ) : (
            <div
              className="flex items-center justify-center rounded-2xl bg-background-secondary text-text-muted text-sm"
              style={{ aspectRatio: '9/16', maxHeight: 480 }}
            >
              Preview will appear here
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Sub-component: Script review ─────────────
function ScriptReview({
  script,
  hook,
  duration,
  onRender,
  loading,
}: {
  script: string;
  hook: string;
  duration: number;
  onRender: () => void;
  loading: boolean;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <span className="badge-purple">Hook</span>
        <p className="text-sm font-semibold text-text-primary">{hook}</p>
      </div>

      <div>
        <label className="text-xs font-semibold text-text-secondary mb-1.5 block">
          Full Script
        </label>
        <textarea
          className="textarea h-48 text-sm font-mono"
          value={script}
          readOnly
        />
      </div>

      <div className="flex items-center gap-4 text-xs text-text-muted">
        <span>~{duration}s estimated duration</span>
        <span>{script.split(' ').length} words</span>
      </div>

      <button
        className="btn-primary w-full justify-center py-3 text-base"
        onClick={onRender}
        disabled={loading}
      >
        {loading ? (
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <Play className="w-5 h-5" />
        )}
        {loading ? 'Starting…' : 'Render Video'}
      </button>
    </div>
  );
}
