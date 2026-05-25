import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, CheckCircle2, XCircle, X } from 'lucide-react';
import { useAppStore, useRenderingJobs } from '@/store';
import clsx from 'clsx';

const STEP_LABELS: Record<string, string> = {
  generating_script: 'Writing script…',
  generating_voice: 'Generating voice…',
  fetching_broll: 'Finding B-roll…',
  compositing: 'Compositing…',
  adding_subtitles: 'Adding subtitles…',
  adding_music: 'Adding music…',
  applying_effects: 'Applying effects…',
  exporting: 'Exporting…',
  done: 'Done!',
  error: 'Error',
};

export default function RenderQueueBar() {
  const jobs = useRenderingJobs();
  const allJobs = useAppStore((s) => s.renderQueue);
  const { removeRenderJob } = useAppStore();

  const recentDone = allJobs.filter(
    (j) => j.status === 'done' || j.status === 'error'
  );

  const visible = [...jobs, ...recentDone.slice(0, 2)];

  if (visible.length === 0) return null;

  return (
    <div className="border-t border-border bg-background-secondary px-6 py-3 flex gap-3 overflow-x-auto shrink-0">
      <AnimatePresence>
        {visible.map((job) => (
          <motion.div
            key={job.job_id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={clsx(
              'flex items-center gap-3 px-4 py-2.5 rounded-xl border min-w-[260px] max-w-xs',
              job.status === 'done'
                ? 'bg-neon-green/10 border-neon-green/30'
                : job.status === 'error'
                  ? 'bg-red-500/10 border-red-500/30'
                  : 'bg-background-card border-border'
            )}
          >
            {/* Icon */}
            {job.status === 'done' ? (
              <CheckCircle2 className="w-4 h-4 text-neon-green shrink-0" />
            ) : job.status === 'error' ? (
              <XCircle className="w-4 h-4 text-red-400 shrink-0" />
            ) : (
              <Loader2 className="w-4 h-4 text-neon-purple animate-spin shrink-0" />
            )}

            {/* Info */}
            <div className="flex flex-col flex-1 min-w-0">
              <span className="text-xs font-semibold text-text-primary truncate">
                {STEP_LABELS[job.status] ?? job.current_step}
              </span>
              {job.status !== 'done' && job.status !== 'error' && (
                <div className="mt-1 h-1 rounded-full bg-background-tertiary overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-neon-purple to-neon-blue"
                    initial={{ width: 0 }}
                    animate={{ width: `${job.progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              )}
              {job.status === 'error' && (
                <span className="text-xs text-red-400 truncate">{job.error}</span>
              )}
            </div>

            {/* Progress % */}
            {job.status !== 'done' && job.status !== 'error' && (
              <span className="text-xs text-text-muted shrink-0">
                {job.progress}%
              </span>
            )}

            {/* Dismiss */}
            {(job.status === 'done' || job.status === 'error') && (
              <button
                onClick={() => removeRenderJob(job.job_id)}
                className="ml-1 text-text-muted hover:text-text-secondary transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
