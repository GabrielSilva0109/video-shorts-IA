import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '@/store';
import type { RenderJob } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws';

export function useRenderSocket() {
  const ws = useRef<WebSocket | null>(null);
  const { updateRenderJob, updateProject } = useAppStore();

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

    ws.current.onclose = () => {
      // Reconnect after 3 s
      setTimeout(connect, 3000);
    };
  }, [updateRenderJob, updateProject]);

  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);

  return ws;
}
