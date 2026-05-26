import { motion } from 'framer-motion';
import type { VideoProject } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  RiCheckboxCircleLine,
  RiLoader4Line,
  RiErrorWarningLine,
  RiTimeLine,
  RiDeleteBinLine,
  RiPlayLine,
} from 'react-icons/ri';
import clsx from 'clsx';

interface Props {
  project: VideoProject;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  active?: boolean;
}

export default function ProjectCard({ project, onSelect, onDelete, active }: Props) {
  const statusIcon = () => {
    switch (project.status) {
      case 'done':    return <RiCheckboxCircleLine className="w-3 h-3" />;
      case 'error':   return <RiErrorWarningLine className="w-3 h-3" />;
      default:
        if (project.progress > 0) return <RiLoader4Line className="w-3 h-3 animate-spin" />;
        return <RiTimeLine className="w-3 h-3" />;
    }
  };

  const badgeClass = {
    done: 'badge-green',
    error: 'badge-red',
  }[project.status] ?? 'badge-accent';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      className={clsx(
        'card-hover p-4 cursor-pointer group relative',
        active && 'border-accent/50'
      )}
      onClick={() => onSelect(project.id)}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <span className={badgeClass}>
          {statusIcon()}
          {project.status.replace(/_/g, ' ')}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(project.id); }}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md text-text-muted hover:text-danger hover:bg-danger/10"
        >
          <RiDeleteBinLine className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Title */}
      <p className="text-sm font-semibold text-text-primary line-clamp-2 mb-1">
        {project.title || project.prompt}
      </p>
      <p className="text-xs text-text-muted capitalize mb-3">
        {project.style.replace(/_/g, ' ')} · {project.platform.replace(/_/g, ' ')}
      </p>

      {/* Progress bar */}
      {project.progress > 0 && project.status !== 'done' && project.status !== 'error' && (
        <div className="h-0.5 rounded-full bg-background-hover overflow-hidden mb-3">
          <motion.div
            className="h-full rounded-full bg-accent"
            animate={{ width: `${project.progress}%` }}
            transition={{ duration: 0.4 }}
          />
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">
          {formatDistanceToNow(new Date(project.created_at), { addSuffix: true, locale: ptBR })}
        </span>
        {project.status === 'done' && (
          <button
            onClick={(e) => { e.stopPropagation(); onSelect(project.id); }}
            className="p-1 rounded-md text-text-muted hover:text-success hover:bg-success/10 transition-colors"
          >
            <RiPlayLine className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </motion.div>
  );
}
