import { motion, AnimatePresence } from 'framer-motion';
import {
  RiLoader4Line,
  RiCheckboxCircleLine,
  RiCloseCircleLine,
  RiCloseLine,
} from 'react-icons/ri';
import { useAppStore, useRenderingJobs } from '@/store';
import clsx from 'clsx';

const STEP_LABELS: Record<string, string> = {
  generating_script: 'Escrevendo script…',
  generating_voice: 'Gerando voz…',
  fetching_broll: 'Buscando imagens…',
  compositing: 'Montando vídeo…',
  adding_subtitles: 'Adicionando legendas…',
  adding_music: 'Adicionando música…',
  applying_effects: 'Aplicando efeitos…',
  exporting: 'Exportando…',
  done: 'Concluído!',
  error: 'Erro',
};

export default function RenderQueueBar() {
  const jobs = useRenderingJobs();
  const allJobs = useAppStore((s) => s.renderQueue);
  const { removeRenderJob } = useAppStore();

  const recentDone = allJobs.filter((j) => j.status === 'done' || j.status === 'error');
  const visible = [...jobs, ...recentDone.slice(0, 2)];

  if (visible.length === 0) return null;

  return (
    <div className="border-t border-border bg-background-secondary px-4 py-2.5 flex gap-2 overflow-x-auto shrink-0">
      <AnimatePresence>
        {visible.map((job) => (
          <motion.div
            key={job.job_id}
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            className={clsx(
              'flex items-center gap-2.5 px-3 py-2 rounded-lg border min-w-[240px] max-w-xs',
              job.status === 'done'
                ? 'bg-success/5 border-success/20'
                : job.status === 'error'
                  ? 'bg-danger/5 border-danger/20'
                  : 'bg-background-card border-border'
            )}
          >
            {job.status === 'done' ? (
              <RiCheckboxCircleLine className="w-4 h-4 text-success shrink-0" />
            ) : job.status === 'error' ? (
              <RiCloseCircleLine className="w-4 h-4 text-danger shrink-0" />
            ) : (
              <RiLoader4Line className="w-4 h-4 text-accent animate-spin shrink-0" />
            )}

            <div className="flex flex-col flex-1 min-w-0">
              <span className="text-xs font-medium text-text-primary truncate">
                {STEP_LABELS[job.status] ?? job.current_step}
              </span>
              {job.status !== 'done' && job.status !== 'error' && (
                <div className="mt-1 h-0.5 rounded-full bg-background-hover overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-accent"
                    initial={{ width: 0 }}
                    animate={{ width: `${job.progress}%` }}
                    transition={{ duration: 0.4 }}
                  />
                </div>
              )}
              {job.status === 'error' && (
                <span className="text-xs text-danger/70 truncate">{job.error}</span>
              )}
            </div>

            {job.status !== 'done' && job.status !== 'error' && (
              <span className="text-xs text-text-muted shrink-0 tabular-nums">{job.progress}%</span>
            )}

            {(job.status === 'done' || job.status === 'error') && (
              <button
                onClick={() => removeRenderJob(job.job_id)}
                className="text-text-muted hover:text-text-secondary transition-colors ml-1"
              >
                <RiCloseLine className="w-3.5 h-3.5" />
              </button>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
