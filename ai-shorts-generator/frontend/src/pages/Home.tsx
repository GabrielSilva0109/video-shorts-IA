import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Wand2,
  TrendingUp,
  Zap,
  Clock,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import { getProjects } from '@/services/videoService';
import { useAppStore } from '@/store';
import ProjectCard from '@components/ProjectCard/ProjectCard';

const STAT_CARDS = [
  {
    label: 'Videos Created',
    icon: CheckCircle2,
    color: 'text-neon-green',
    key: 'done',
  },
  {
    label: 'In Progress',
    icon: Clock,
    color: 'text-neon-purple',
    key: 'rendering',
  },
  {
    label: 'Failed',
    icon: AlertTriangle,
    color: 'text-red-400',
    key: 'error',
  },
  {
    label: 'Total Generated',
    icon: TrendingUp,
    color: 'text-neon-blue',
    key: 'total',
  },
];

export default function Home() {
  const { setProjects, projects, setActiveProject, removeProject } = useAppStore();

  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  useEffect(() => {
    if (data) setProjects(data);
  }, [data, setProjects]);

  const stats = {
    done: projects.filter((p) => p.status === 'done').length,
    rendering: projects.filter(
      (p) => p.status !== 'done' && p.status !== 'error' && p.status !== 'idle'
    ).length,
    error: projects.filter((p) => p.status === 'error').length,
    total: projects.length,
  };

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto">
      {/* ── Hero header ─────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-3"
      >
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="badge-purple">AI Shorts Generator</span>
        </div>
        <h1 className="text-4xl font-display font-bold">
          Create{' '}
          <span className="gradient-text">Viral Short Videos</span>{' '}
          with AI
        </h1>
        <p className="text-text-secondary max-w-xl">
          Turn any topic into a professionally edited short video in under 2
          minutes. Scripts, voice, B-roll, subtitles and music — fully automated.
        </p>
        <div className="flex gap-3 mt-2">
          <Link to="/generator" className="btn-primary">
            <Wand2 className="w-4 h-4" /> New Video
          </Link>
          <Link to="/templates" className="btn-secondary">
            Browse Templates
          </Link>
        </div>
      </motion.div>

      {/* ── Stats ───────────────────────────── */}
      <div className="grid grid-cols-4 gap-3">
        {STAT_CARDS.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.key}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              className="card p-4 flex flex-col gap-1"
            >
              <Icon className={`w-4 h-4 ${card.color}`} />
              <span className="text-2xl font-bold font-display">
                {stats[card.key as keyof typeof stats]}
              </span>
              <span className="text-xs text-text-muted">{card.label}</span>
            </motion.div>
          );
        })}
      </div>

      {/* ── Recent projects ──────────────────── */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-display font-semibold">Recent Projects</h2>
          {projects.length > 0 && (
            <Link to="/generator" className="btn-ghost text-xs">
              + New Video
            </Link>
          )}
        </div>

        {isLoading ? (
          <div className="grid grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="skeleton h-36 rounded-2xl" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="card p-12 flex flex-col items-center gap-4 text-center">
            <div className="w-16 h-16 rounded-2xl bg-neon-purple/10 flex items-center justify-center">
              <Wand2 className="w-7 h-7 text-neon-purple" />
            </div>
            <div>
              <p className="font-semibold text-text-primary mb-1">
                No videos yet
              </p>
              <p className="text-sm text-text-muted">
                Generate your first AI short video to get started.
              </p>
            </div>
            <Link to="/generator" className="btn-primary">
              <Wand2 className="w-4 h-4" /> Create First Video
            </Link>
          </div>
        ) : (
          <AnimatePresence>
            <div className="grid grid-cols-3 gap-3">
              {projects.slice(0, 9).map((p) => (
                <ProjectCard
                  key={p.id}
                  project={p}
                  onSelect={setActiveProject}
                  onDelete={removeProject}
                />
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
