import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { ListVideo, Plus, Trash2, Play, Upload } from 'lucide-react';
import { createProject, startRender } from '@/services/videoService';
import { useAppStore } from '@/store';
import type { VideoStyle, ExportPlatform } from '@/types';

interface BatchItem {
  id: string;
  prompt: string;
  style: VideoStyle;
  platform: ExportPlatform;
  status: 'pending' | 'queued' | 'done' | 'error';
}

let itemCounter = 0;
const newItem = (): BatchItem => ({
  id: `item-${++itemCounter}`,
  prompt: '',
  style: 'hormozi',
  platform: 'tiktok',
  status: 'pending',
});

export default function BatchGenerator() {
  const [items, setItems] = useState<BatchItem[]>([newItem()]);
  const { draftRequest, addProject, addRenderJob } = useAppStore();

  const updateItem = (id: string, partial: Partial<BatchItem>) =>
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, ...partial } : item))
    );

  const removeItem = (id: string) =>
    setItems((prev) => prev.filter((i) => i.id !== id));

  const batchMutation = useMutation({
    mutationFn: async () => {
      const pending = items.filter(
        (i) => i.status === 'pending' && i.prompt.trim()
      );
      for (const item of pending) {
        updateItem(item.id, { status: 'queued' });
        try {
          const project = await createProject({
            prompt: item.prompt,
            style: item.style,
            platform: item.platform,
            voice_model: draftRequest.voice_model ?? 'openai',
            subtitle_style: draftRequest.subtitle_style ?? 'hormozi',
            language: draftRequest.language ?? 'en',
            effects: draftRequest.effects!,
          });
          addProject(project);
          const job = await startRender(project.id);
          addRenderJob(job);
          updateItem(item.id, { status: 'done' });
        } catch {
          updateItem(item.id, { status: 'error' });
        }
      }
    },
    onSuccess: () => toast.success('Batch render started!'),
    onError: () => toast.error('Some items failed to queue'),
  });

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <ListVideo className="w-6 h-6 text-neon-purple" />
        <h1 className="text-2xl font-display font-bold">Batch Generator</h1>
        <span className="badge-purple ml-2">{items.length} videos</span>
        <div className="flex gap-2 ml-auto">
          <button
            className="btn-secondary text-sm"
            onClick={() => setItems((p) => [...p, newItem()])}
          >
            <Plus className="w-4 h-4" /> Add Row
          </button>
          <button
            className="btn-primary text-sm"
            onClick={() => batchMutation.mutate()}
            disabled={
              batchMutation.isPending ||
              items.every((i) => !i.prompt.trim())
            }
          >
            <Play className="w-4 h-4" />
            {batchMutation.isPending ? 'Processing…' : 'Render All'}
          </button>
        </div>
      </div>

      {/* ── Hint ─────────────────────────────── */}
      <p className="text-sm text-text-muted">
        Add multiple prompts to generate and render them sequentially. Each
        video is processed with the global settings from the Generator page.
      </p>

      {/* ── Items ───────────────────────────── */}
      <div className="flex flex-col gap-3">
        {items.map((item, idx) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="card p-4 flex items-start gap-3"
          >
            <span className="text-xs text-text-muted w-5 pt-2.5 shrink-0 text-center">
              {idx + 1}
            </span>

            <input
              className="input flex-1 text-sm"
              placeholder="Enter topic or prompt…"
              value={item.prompt}
              onChange={(e) => updateItem(item.id, { prompt: e.target.value })}
            />

            <select
              className="input w-36 text-xs"
              value={item.style}
              onChange={(e) =>
                updateItem(item.id, { style: e.target.value as VideoStyle })
              }
            >
              {['hormozi', 'tiktok_story', 'finance', 'motivation', 'gaming', 'luxury', 'documentary'].map((s) => (
                <option key={s} value={s}>
                  {s.replace(/_/g, ' ')}
                </option>
              ))}
            </select>

            <select
              className="input w-36 text-xs"
              value={item.platform}
              onChange={(e) =>
                updateItem(item.id, { platform: e.target.value as ExportPlatform })
              }
            >
              <option value="tiktok">TikTok</option>
              <option value="youtube_shorts">YT Shorts</option>
              <option value="instagram_reels">Reels</option>
            </select>

            {/* Status pill */}
            <span
              className={
                item.status === 'done'
                  ? 'badge-green'
                  : item.status === 'error'
                    ? 'badge bg-red-500/15 text-red-400 border-red-500/30'
                    : item.status === 'queued'
                      ? 'badge-blue'
                      : 'badge bg-background-tertiary text-text-muted border-border'
              }
            >
              {item.status}
            </span>

            <button
              className="btn-ghost p-1.5 text-text-muted hover:text-red-400"
              onClick={() => removeItem(item.id)}
              disabled={items.length === 1}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </motion.div>
        ))}
      </div>

      {/* ── Import from CSV ──────────────────── */}
      <div className="card p-4 border-dashed flex items-center gap-3 text-text-muted hover:border-border-light transition-colors cursor-pointer">
        <Upload className="w-4 h-4" />
        <span className="text-sm">Import prompts from CSV file</span>
      </div>
    </div>
  );
}
