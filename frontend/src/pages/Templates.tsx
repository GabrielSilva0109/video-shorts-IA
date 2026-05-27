import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Layers, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getTemplates } from '@/services/videoService';
import { useAppStore } from '@/store';
import type { VideoTemplate } from '@/types';

const STYLE_COLORS: Record<string, string> = {
  hormozi: 'badge-purple',
  tiktok_story: 'badge-pink',
  finance: 'badge-green',
  motivation: 'bg-orange-500/15 text-orange-400 border-orange-500/30 badge',
  gaming: 'badge-blue',
  luxury: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30 badge',
  documentary: 'bg-slate-500/15 text-slate-400 border-slate-500/30 badge',
};

export default function Templates() {
  const { setDraftRequest } = useAppStore();

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: getTemplates,
  });

  const applyTemplate = (t: VideoTemplate) => {
    setDraftRequest({
      style: t.style,
      effects: t.default_effects,
      subtitle_style: t.default_subtitle_style,
    });
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Layers className="w-6 h-6 text-neon-purple" />
        <h1 className="text-2xl font-display font-bold">Templates</h1>
        <span className="badge-purple ml-auto">{templates.length} templates</span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton h-48 rounded-2xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {templates.map((t, i) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="card-hover p-5 flex flex-col gap-3"
            >
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <span className={STYLE_COLORS[t.style] ?? 'badge-blue'}>
                    {t.style.replace(/_/g, ' ')}
                  </span>
                  <h3 className="mt-2 font-display font-semibold text-text-primary">
                    {t.name}
                  </h3>
                </div>
              </div>

              <p className="text-sm text-text-secondary line-clamp-2">
                {t.description}
              </p>

              {/* Example prompts */}
              {t.prompt_examples.slice(0, 2).map((ex, j) => (
                <p key={j} className="text-xs text-text-muted italic line-clamp-1">
                  "{ex}"
                </p>
              ))}

              {/* Tags */}
              <div className="flex flex-wrap gap-1 mt-auto">
                {t.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-0.5 rounded-md bg-background-tertiary text-text-muted"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* CTA */}
              <Link
                to="/generator"
                onClick={() => applyTemplate(t)}
                className="btn-secondary text-xs justify-center"
              >
                Use Template <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
