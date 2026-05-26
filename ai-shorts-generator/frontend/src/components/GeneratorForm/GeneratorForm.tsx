import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Wand2,
  Mic,
  Music,
  Zap,
  ChevronDown,
  ChevronUp,
  ToggleLeft,
  ToggleRight,
  Globe,
} from 'lucide-react';
import { useAppStore } from '@/store';
import type { VideoStyle, ExportPlatform, SubtitleStyle, VoiceModel } from '@/types';
import clsx from 'clsx';

const STYLES: { value: VideoStyle; label: string; emoji: string }[] = [
  { value: 'hormozi', label: 'Hormozi', emoji: '💥' },
  { value: 'tiktok_story', label: 'TikTok Story', emoji: '📱' },
  { value: 'finance', label: 'Finance', emoji: '💰' },
  { value: 'motivation', label: 'Motivation', emoji: '🔥' },
  { value: 'gaming', label: 'Gaming', emoji: '🎮' },
  { value: 'luxury', label: 'Luxury', emoji: '✨' },
  { value: 'documentary', label: 'Documentary', emoji: '🎬' },
];

const PLATFORMS: { value: ExportPlatform; label: string }[] = [
  { value: 'tiktok', label: 'TikTok' },
  { value: 'youtube_shorts', label: 'YouTube Shorts' },
  { value: 'instagram_reels', label: 'Instagram Reels' },
];

const SUBTITLE_STYLES: { value: SubtitleStyle; label: string }[] = [
  { value: 'hormozi', label: 'Hormozi Bold' },
  { value: 'tiktok', label: 'TikTok Classic' },
  { value: 'clean', label: 'Clean White' },
  { value: 'fire', label: 'Fire 🔥' },
  { value: 'minimal', label: 'Minimal' },
  { value: 'emoji', label: 'Emoji Style' },
];

const VOICES: { value: VoiceModel; label: string }[] = [
  { value: 'openai', label: 'OpenAI TTS' },
  { value: 'elevenlabs', label: 'ElevenLabs' },
  { value: 'local', label: 'Local (Coqui)' },
];

const LANGUAGES = [
  { value: 'pt', label: 'Português', flag: '🇧🇷' },
  { value: 'en', label: 'English', flag: '🇺🇸' },
];

export default function GeneratorForm({
  onSubmit,
  loading,
}: {
  onSubmit: () => void;
  loading: boolean;
}) {
  const { draftRequest, setDraftRequest, setDraftEffects } = useAppStore();
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const effects = draftRequest.effects!;

  return (
    <div className="flex flex-col gap-6">
      {/* ── Prompt ──────────────────────────── */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-semibold text-text-primary">
          Topic / Prompt
        </label>
        <textarea
          className="textarea h-28"
          placeholder="e.g. 'The dark truth about compound interest that banks don't want you to know…'"
          value={draftRequest.prompt ?? ''}
          onChange={(e) => setDraftRequest({ prompt: e.target.value })}
        />
      </div>

      {/* ── Style ───────────────────────────── */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-semibold text-text-primary">
          Video Style
        </label>
        <div className="grid grid-cols-4 gap-2">
          {STYLES.map((s) => (
            <button
              key={s.value}
              onClick={() => setDraftRequest({ style: s.value })}
              className={clsx(
                'flex flex-col items-center gap-1 p-3 rounded-xl border text-xs font-medium transition-all duration-150',
                draftRequest.style === s.value
                  ? 'bg-neon-purple/15 border-neon-purple/50 text-neon-purple'
                  : 'bg-background-secondary border-border text-text-secondary hover:border-border-light hover:text-text-primary'
              )}
            >
              <span className="text-xl">{s.emoji}</span>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Platform + Language ──────────────── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-2">
          <label className="text-sm font-semibold text-text-primary">Platform</label>
          <div className="flex flex-col gap-1.5">
            {PLATFORMS.map((p) => (
              <button
                key={p.value}
                onClick={() => setDraftRequest({ platform: p.value })}
                className={clsx(
                  'py-2 rounded-xl border text-sm font-medium transition-all duration-150',
                  draftRequest.platform === p.value
                    ? 'bg-neon-blue/15 border-neon-blue/50 text-neon-blue'
                    : 'bg-background-secondary border-border text-text-secondary hover:border-border-light'
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
            <Globe className="w-4 h-4" /> Language
          </label>
          <div className="flex flex-col gap-1.5">
            {LANGUAGES.map((l) => (
              <button
                key={l.value}
                onClick={() => setDraftRequest({ language: l.value })}
                className={clsx(
                  'py-2 rounded-xl border text-sm font-medium transition-all duration-150 flex items-center justify-center gap-2',
                  draftRequest.language === l.value
                    ? 'bg-neon-purple/15 border-neon-purple/50 text-neon-purple'
                    : 'bg-background-secondary border-border text-text-secondary hover:border-border-light'
                )}
              >
                <span>{l.flag}</span>
                {l.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Advanced toggle ──────────────────── */}
      <button
        className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
        onClick={() => setAdvancedOpen((v) => !v)}
      >
        {advancedOpen ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
        Advanced Settings
      </button>

      {advancedOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="flex flex-col gap-4 overflow-hidden"
        >
          {/* Voice + Subtitle row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary flex items-center gap-1">
                <Mic className="w-3 h-3" /> Voice
              </label>
              <select
                className="input text-sm"
                value={draftRequest.voice_model}
                onChange={(e) =>
                  setDraftRequest({ voice_model: e.target.value as VoiceModel })
                }
              >
                {VOICES.map((v) => (
                  <option key={v.value} value={v.value}>
                    {v.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary flex items-center gap-1">
                <Zap className="w-3 h-3" /> Subtitles
              </label>
              <select
                className="input text-sm"
                value={draftRequest.subtitle_style}
                onChange={(e) =>
                  setDraftRequest({
                    subtitle_style: e.target.value as SubtitleStyle,
                  })
                }
              >
                {SUBTITLE_STYLES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Background music */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-text-secondary flex items-center gap-1">
              <Music className="w-3 h-3" /> Background Music
            </label>
            <input
              className="input text-sm"
              placeholder="auto — or paste URL / filename"
              value={draftRequest.background_music ?? ''}
              onChange={(e) =>
                setDraftRequest({ background_music: e.target.value })
              }
            />
          </div>

          {/* Effects toggles */}
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold text-text-secondary">
              Effects
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(
                Object.keys(effects) as (keyof typeof effects)[]
              ).map((key) => (
                <button
                  key={key}
                  onClick={() => setDraftEffects({ [key]: !effects[key] })}
                  className="flex items-center justify-between px-3 py-2 rounded-xl bg-background-secondary border border-border hover:border-border-light transition-colors"
                >
                  <span className="text-xs text-text-secondary capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  {effects[key] ? (
                    <ToggleRight className="w-4 h-4 text-neon-purple" />
                  ) : (
                    <ToggleLeft className="w-4 h-4 text-text-muted" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* ── Submit ──────────────────────────── */}
      <button
        className="btn-primary w-full justify-center py-3 text-base"
        onClick={onSubmit}
        disabled={loading || !draftRequest.prompt?.trim()}
      >
        {loading ? (
          <>
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Generating…
          </>
        ) : (
          <>
            <Wand2 className="w-5 h-5" />
            Generate Short
          </>
        )}
      </button>
    </div>
  );
}
