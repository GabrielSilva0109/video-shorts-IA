import { motion } from 'framer-motion';
import type { VideoProject } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import {
  CheckCircle2,
  Loader2,
  AlertCircle,
  Clock,
  Trash2,
  Play,
} from 'lucide-react';
import clsx from 'clsx';

const STATUS_COLORS: Record<string, string> = {
  done: 'badge-green',
  error: 'bg-red-500/15 text-red-400 border-red-500/30 badge',
  idle: 'badge-purple',
};

interface Props {
  project: VideoProject;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  active?: boolean;
}

export default function ProjectCard({ project, onSelect, onDelete, active }: Props) {
  const statusIcon = () => {
    switch (project.status) {
      case 'done':
        return <CheckCircle2 className="w-3.5 h-3.5" />;
      case 'error':
        return <AlertCircle className="w-3.5 h-3.5" />;
      default:
        if (project.progress > 0)
          return <Loader2 className="w-3.5 h-3.5 animate-spin" />;
        return <Clock className="w-3.5 h-3.5" />;
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={clsx(
        'card-hover p-4 cursor-pointer group relative',
        active && 'border-neon-purple/50 shadow-neon-purple'
      )}
      onClick={() => onSelect(project.id)}
    >
      {/* Status badge */}
      <div className="flex items-center justify-between mb-3">
        <span
          className={
            STATUS_COLORS[project.status] ??
            'badge bg-neon-blue/15 text-neon-blue border-neon-blue/30'
          }
        >
          {statusIcon()}
          {project.status.replace(/_/g, ' ')}
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(project.id);
          }}
          className="opacity-0 group-hover:opacity-100 transition-opacity btn-ghost p-1.5 text-text-muted hover:text-red-400"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Title */}
      <p className="text-sm font-semibold text-text-primary line-clamp-2 mb-1">
        {project.title || project.prompt}
      </p>
      <p className="text-xs text-text-muted capitalize mb-3">
        {project.style.replace(/_/g, ' ')} · {project.platform.replace(/_/g, ' ')}
      </p>

      {/* Progress bar if rendering */}
      {project.progress > 0 && project.status !== 'done' && project.status !== 'error' && (
        <div className="h-1 rounded-full bg-background-tertiary overflow-hidden mb-2">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-neon-purple to-neon-blue"
            animate={{ width: `${project.progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">
          {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
        </span>
        {project.status === 'done' && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect(project.id);
            }}
            className="btn-ghost p-1.5"
          >
            <Play className="w-3.5 h-3.5 text-neon-green" />
          </button>
        )}
      </div>
    </motion.div>
  );
}
