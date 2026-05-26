import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  RiMagicLine,
  RiMicLine,
  RiMusicLine,
  RiGlobalLine,
  RiArrowDownSLine,
  RiArrowUpSLine,
  RiToggleLine,
  RiToggleFill,
  RiLoader4Line,
  RiFireLine,
  RiSmartphoneLine,
  RiLineChartLine,
  RiFlashlightLine,
  RiGamepadLine,
  RiVipCrownLine,
  RiFilmLine,
} from 'react-icons/ri';
import { useAppStore } from '@/store';
import type { VideoStyle, ExportPlatform, SubtitleStyle, VoiceModel } from '@/types';
import clsx from 'clsx';

const STYLES: { value: VideoStyle; label: string; icon: React.ElementType }[] = [
  { value: 'hormozi', label: 'Hormozi', icon: RiFireLine },
  { value: 'tiktok_story', label: 'TikTok Story', icon: RiSmartphoneLine },
  { value: 'finance', label: 'Finance', icon: RiLineChartLine },
  { value: 'motivation', label: 'Motivação', icon: RiFlashlightLine },
  { value: 'gaming', label: 'Gaming', icon: RiGamepadLine },
  { value: 'luxury', label: 'Luxury', icon: RiVipCrownLine },
  { value: 'documentary', label: 'Documentário', icon: RiFilmLine },
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
  { value: 'fire', label: 'Fire' },
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

export default function GeneratorForm({ onSubmit, loading }: { onSubmit: () => void; loading: boolean }) {
  const { draftRequest, setDraftRequest, setDraftEffects } = useAppStore();
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const effects = draftRequest.effects!;

  return (
    <div className="flex flex-col gap-5">
      {/* Prompt */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-text-primary">Tópico / Prompt</label>
        <textarea
          className="textarea h-24"
          placeholder="Ex: A verdade sombria sobre juros compostos que os bancos não querem que você saiba"
          value={draftRequest.prompt ?? ''}
          onChange={(e) => setDraftRequest({ prompt: e.target.value })}
        />
      </div>

      {/* Style */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-text-primary">Estilo do Vídeo</label>
        <div className="grid grid-cols-4 gap-1.5">
          {STYLES.map((s) => (
            <button
              key={s.value}
              onClick={() => setDraftRequest({ style: s.value })}
              className={clsx(
                'flex flex-col items-center gap-1 p-2.5 rounded-lg border text-xs font-medium transition-all duration-150',
                draftRequest.style === s.value
                  ? 'bg-accent/10 border-accent/40 text-accent'
                  : 'bg-background-secondary border-border text-text-secondary hover:border-border-light hover:text-text-primary'
              )}
            >
              <s.icon className="w-4 h-4" />
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Platform + Language */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-text-primary">Plataforma</label>
          <div className="flex flex-col gap-1">
            {PLATFORMS.map((p) => (
              <button
                key={p.value}
                onClick={() => setDraftRequest({ platform: p.value })}
                className={clsx(
                  'py-1.5 rounded-lg border text-xs font-medium transition-all duration-150',
                  draftRequest.platform === p.value
                    ? 'bg-accent/10 border-accent/40 text-accent'
                    : 'bg-background-secondary border-border text-text-secondary hover:border-border-light'
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-text-primary flex items-center gap-1">
            <RiGlobalLine className="w-3.5 h-3.5" /> Idioma
          </label>
          <div className="flex flex-col gap-1">
            {LANGUAGES.map((l) => (
              <button
                key={l.value}
                onClick={() => setDraftRequest({ language: l.value })}
                className={clsx(
                  'py-1.5 rounded-lg border text-xs font-medium transition-all duration-150 flex items-center justify-center gap-1.5',
                  draftRequest.language === l.value
                    ? 'bg-accent/10 border-accent/40 text-accent'
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

      {/* Advanced toggle */}
      <button
        className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
        onClick={() => setAdvancedOpen((v) => !v)}
      >
        {advancedOpen ? <RiArrowUpSLine className="w-3.5 h-3.5" /> : <RiArrowDownSLine className="w-3.5 h-3.5" />}
        Configurações avançadas
      </button>

      {advancedOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="flex flex-col gap-4 overflow-hidden"
        >
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-text-muted flex items-center gap-1">
                <RiMicLine className="w-3 h-3" /> Voz
              </label>
              <select
                className="input text-xs"
                value={draftRequest.voice_model}
                onChange={(e) => setDraftRequest({ voice_model: e.target.value as VoiceModel })}
              >
                {VOICES.map((v) => (
                  <option key={v.value} value={v.value}>{v.label}</option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-text-muted">Legendas</label>
              <select
                className="input text-xs"
                value={draftRequest.subtitle_style}
                onChange={(e) => setDraftRequest({ subtitle_style: e.target.value as SubtitleStyle })}
              >
                {SUBTITLE_STYLES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-text-muted flex items-center gap-1">
              <RiMusicLine className="w-3 h-3" /> Música de Fundo
            </label>
            <input
              className="input text-xs"
              placeholder="auto — ou cole URL / nome do arquivo"
              value={draftRequest.background_music ?? ''}
              onChange={(e) => setDraftRequest({ background_music: e.target.value })}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-muted">Efeitos</label>
            <div className="grid grid-cols-2 gap-1.5">
              {(Object.keys(effects) as (keyof typeof effects)[]).map((key) => (
                <button
                  key={key}
                  onClick={() => setDraftEffects({ [key]: !effects[key] })}
                  className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-background-secondary border border-border hover:border-border-light transition-colors"
                >
                  <span className="text-xs text-text-secondary capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  {effects[key]
                    ? <RiToggleFill className="w-4 h-4 text-accent" />
                    : <RiToggleLine className="w-4 h-4 text-text-muted" />
                  }
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Submit */}
      <button
        className="btn-primary w-full justify-center py-2.5 text-sm"
        onClick={onSubmit}
        disabled={loading || !draftRequest.prompt?.trim()}
      >
        {loading ? (
          <>
            <RiLoader4Line className="w-4 h-4 animate-spin" />
            Gerando...
          </>
        ) : (
          <>
            <RiMagicLine className="w-4 h-4" />
            Gerar Short
          </>
        )}
      </button>
    </div>
  );
}
