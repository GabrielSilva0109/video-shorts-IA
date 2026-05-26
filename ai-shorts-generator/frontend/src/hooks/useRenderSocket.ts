import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '@/store';
import { getRenderStatus, getProject } from '@/services/videoService';
import type { RenderJob } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws';
const TERMINAL = new Set(['done', 'error']);
const POLL_MS = 2000;

export function useRenderSocket() {
  const ws = useRef<WebSocket | null>(null);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const { updateRenderJob, updateProject } = useAppStore();

  // ── HTTP polling (reliable fallback) ──────────────────────────────────────
  const pollActiveJobs = useCallback(async () => {
    const activeJobs = useAppStore.getState().renderQueue.filter(
      (j) => !TERMINAL.has(j.status)
    );
    for (const job of activeJobs) {
      try {
        const updated = await getRenderStatus(job.job_id);
        updateRenderJob(updated.job_id, updated);
        if (TERMINAL.has(updated.status)) {
          // Job finished — fetch full project to get output_path / thumbnail_path
          try {
            const fullProject = await getProject(updated.project_id);
            useAppStore.getState().updateProject(fullProject.id, fullProject);
          } catch { /* ignore */ }
        } else {
          updateProject(updated.project_id, {
            status: updated.status,
            progress: updated.progress,
          });
        }
      } catch {
        // job might not exist yet — ignore
      }
    }
  }, [updateRenderJob, updateProject]);

  useEffect(() => {
    pollTimer.current = setInterval(pollActiveJobs, POLL_MS);
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
  }, [pollActiveJobs]);

  // ── WebSocket (best-effort real-time updates) ─────────────────────────────
  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    ws.current = new WebSocket(`${WS_URL}/render`);

    ws.current.onmessage = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data as string) as {
          type: 'job_update' | 'project_update';
          payload: RenderJob;
        };
        if (data.type === 'job_update') {
          updateRenderJob(data.payload.job_id, data.payload);
          updateProject(data.payload.project_id, {
            status: data.payload.status,
            progress: data.payload.progress,
          });
        }
      } catch {
        // malformed message — ignore
      }
    };

    ws.current.onclose = () => setTimeout(connect, 3000);
  }, [updateRenderJob, updateProject]);

  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);

  return ws;
}
