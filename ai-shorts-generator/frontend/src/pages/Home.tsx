import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import {
  RiVideoAddLine,
  RiTrendingUpLine,
  RiCheckboxCircleLine,
  RiErrorWarningLine,
  RiTimeLine,
  RiFlashlightLine,
} from 'react-icons/ri';
import { getProjects } from '@/services/videoService';
import { useAppStore } from '@/store';
import ProjectCard from '@components/ProjectCard/ProjectCard';

const STAT_CARDS = [
  { label: 'Criados', icon: RiCheckboxCircleLine, color: 'text-success', key: 'done' },
  { label: 'Em andamento', icon: RiTimeLine, color: 'text-accent', key: 'rendering' },
  { label: 'Com erro', icon: RiErrorWarningLine, color: 'text-danger', key: 'error' },
  { label: 'Total', icon: RiTrendingUpLine, color: 'text-text-secondary', key: 'total' },
];

export default function Home() {
  const { setProjects, projects, setActiveProject, removeProject } = useAppStore();
  const navigate = useNavigate();

  const handleSelectProject = (id: string) => {
    setActiveProject(id);
    navigate('/generator');
  };

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
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-3"
      >
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
            <RiFlashlightLine className="w-4 h-4 text-white" />
          </div>
          <span className="text-xs font-medium text-text-muted tracking-wide uppercase">AI Shorts Generator</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          Crie vídeos curtos com IA
        </h1>
        <p className="text-text-secondary text-sm max-w-xl leading-relaxed">
          Transforme qualquer tópico em um short profissional em menos de 2 minutos.
          Script, voz, imagens, legendas e música — totalmente automatizado.
        </p>
        <div className="flex gap-2 mt-1">
          <Link to="/generator" className="btn-primary">
            <RiVideoAddLine className="w-4 h-4" /> Novo Vídeo
          </Link>
          <Link to="/templates" className="btn-secondary">
            Ver Templates
          </Link>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {STAT_CARDS.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.key}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="card p-4 flex flex-col gap-2"
            >
              <Icon className={`w-4 h-4 ${card.color}`} />
              <span className="text-2xl font-bold tabular-nums">
                {stats[card.key as keyof typeof stats]}
              </span>
              <span className="text-xs text-text-muted">{card.label}</span>
            </motion.div>
          );
        })}
      </div>

      {/* Recent projects */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-text-primary">Projetos recentes</h2>
          {projects.length > 0 && (
            <Link to="/generator" className="btn-ghost text-xs">
              + Novo Vídeo
            </Link>
          )}
        </div>

        {isLoading ? (
          <div className="grid grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="skeleton h-32 rounded-xl" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="card p-12 flex flex-col items-center gap-4 text-center">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
              <RiVideoAddLine className="w-6 h-6 text-accent" />
            </div>
            <div>
              <p className="font-semibold text-text-primary mb-1">Nenhum vídeo ainda</p>
              <p className="text-sm text-text-muted">
                Gere seu primeiro short com IA para começar.
              </p>
            </div>
            <Link to="/generator" className="btn-primary">
              <RiVideoAddLine className="w-4 h-4" /> Criar Primeiro Vídeo
            </Link>
          </div>
        ) : (
          <AnimatePresence>
            <div className="grid grid-cols-3 gap-3">
              {projects.slice(0, 9).map((p) => (
                <ProjectCard
                  key={p.id}
                  project={p}
                  onSelect={handleSelectProject}
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
