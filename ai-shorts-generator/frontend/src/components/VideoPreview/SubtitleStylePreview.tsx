import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '@/store';

const STYLE_CONFIGS: Record<string, {
  fontSize: number;
  fontWeight: number;
  color: string;
  textShadow: string;
  background?: string;
  padding?: string;
  borderRadius?: number;
  uppercase: boolean;
  letterSpacing?: string;
}> = {
  hormozi: {
    fontSize: 22,
    fontWeight: 900,
    color: '#ffffff',
    textShadow: '3px 3px 0 #000,-3px 3px 0 #000,3px -3px 0 #000,-3px -3px 0 #000',
    uppercase: true,
    letterSpacing: '-0.01em',
  },
  tiktok: {
    fontSize: 18,
    fontWeight: 700,
    color: '#ffffff',
    textShadow: '0 2px 8px rgba(0,0,0,0.9)',
    background: 'rgba(0,0,0,0.55)',
    padding: '4px 14px',
    borderRadius: 4,
    uppercase: false,
  },
  clean: {
    fontSize: 16,
    fontWeight: 500,
    color: '#ffffff',
    textShadow: '0 1px 4px rgba(0,0,0,0.7)',
    uppercase: false,
  },
  fire: {
    fontSize: 22,
    fontWeight: 900,
    color: '#facc15',
    textShadow: '3px 3px 0 #b91c1c,-3px 3px 0 #b91c1c,3px -3px 0 #b91c1c,-3px -3px 0 #b91c1c',
    uppercase: true,
    letterSpacing: '-0.01em',
  },
  minimal: {
    fontSize: 14,
    fontWeight: 400,
    color: 'rgba(255,255,255,0.9)',
    textShadow: '0 1px 2px rgba(0,0,0,0.4)',
    uppercase: false,
  },
  emoji: {
    fontSize: 18,
    fontWeight: 700,
    color: '#ffffff',
    textShadow: '0 2px 6px rgba(0,0,0,0.7)',
    background: 'rgba(0,0,0,0.4)',
    padding: '4px 14px',
    borderRadius: 4,
    uppercase: false,
  },
};

const FALLBACK_LINES = ['DINHEIRO', 'MUDA TUDO'];

export default function SubtitleStylePreview() {
  const { draftRequest } = useAppStore();
  const style = draftRequest.subtitle_style ?? 'hormozi';
  const position = draftRequest.subtitle_position ?? 'center';
  const prompt = draftRequest.prompt?.trim();

  const cfg = STYLE_CONFIGS[style] ?? STYLE_CONFIGS.hormozi;

  // Build 2 short sample lines from prompt or fallback
  const words = prompt ? prompt.split(/\s+/).filter(Boolean) : FALLBACK_LINES;
  const line1 = words.slice(0, 3).join(' ');
  const line2 = words.slice(3, 6).join(' ');

  const fmt = (t: string) => (cfg.uppercase ? t.toUpperCase() : t);

  const posStyle: React.CSSProperties =
    position === 'top'
      ? { top: '20%', transform: 'translateX(-50%)' }
      : position === 'bottom'
      ? { bottom: '20%', transform: 'translateX(-50%)' }
      : { top: '50%', transform: 'translate(-50%, -50%)' };

  const spanStyle: React.CSSProperties = {
    display: 'inline-block',
    fontSize: cfg.fontSize,
    fontWeight: cfg.fontWeight,
    color: cfg.color,
    textShadow: cfg.textShadow,
    background: cfg.background,
    padding: cfg.padding,
    borderRadius: cfg.borderRadius,
    lineHeight: 1.3,
    letterSpacing: cfg.letterSpacing,
    maxWidth: '100%',
  };

  return (
    <div className="flex flex-col gap-2">
      <div
        className="relative rounded-xl overflow-hidden"
        style={{ aspectRatio: '9/16', maxHeight: 480, background: '#0f172a' }}
      >
        {/* Simulated video background */}
        <div
          className="absolute inset-0"
          style={{
            background:
              'linear-gradient(145deg, #1e293b 0%, #0f172a 45%, #1e1b4b 100%)',
          }}
        />
        {/* Subtle grain */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.07]"
          style={{
            backgroundImage:
              'repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(255,255,255,0.15) 3px,rgba(255,255,255,0.15) 4px)',
          }}
        />

        {/* Animated subtitle text */}
        <AnimatePresence mode="wait">
          <motion.div
            key={`${style}|${position}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute left-1/2 text-center"
            style={{ ...posStyle, width: '85%' }}
          >
            <span style={spanStyle}>{fmt(line1)}</span>
            {line2 && (
              <>
                <br />
                <span style={spanStyle}>{fmt(line2)}</span>
              </>
            )}
          </motion.div>
        </AnimatePresence>

        {/* PREVIEW badge */}
        <div
          className="absolute bottom-2 right-3 font-bold tracking-widest text-white/20"
          style={{ fontSize: 9 }}
        >
          PREVIEW
        </div>
      </div>

      <p className="text-[10px] text-text-muted text-center leading-relaxed">
        Visualização do estilo de legenda · não representa o vídeo final
      </p>
    </div>
  );
}
