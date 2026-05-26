// ─────────────────────────────────────────────
//  Core Domain Types
// ─────────────────────────────────────────────

export type VideoStyle =
  | 'hormozi'
  | 'tiktok_story'
  | 'finance'
  | 'motivation'
  | 'gaming'
  | 'luxury'
  | 'documentary';

export type ExportPlatform = 'tiktok' | 'youtube_shorts' | 'instagram_reels';

export type RenderStatus =
  | 'idle'
  | 'queued'
  | 'generating_script'
  | 'generating_voice'
  | 'fetching_broll'
  | 'compositing'
  | 'adding_subtitles'
  | 'adding_music'
  | 'applying_effects'
  | 'exporting'
  | 'done'
  | 'error';

export type SubtitleStyle =
  | 'hormozi'
  | 'tiktok'
  | 'clean'
  | 'fire'
  | 'minimal'
  | 'emoji';

export type SubtitlePosition = 'top' | 'center' | 'bottom';

export type VoiceModel = 'openai' | 'elevenlabs' | 'local';

// ── Script ──────────────────────────────────
export interface ScriptSegment {
  id: string;
  text: string;
  startTime: number;
  endTime: number;
  isBold?: boolean;
  isHook?: boolean;
  emoji?: string;
}

export interface GeneratedScript {
  hook: string;
  body: string;
  cta: string;
  full_text: string;
  segments: ScriptSegment[];
  estimated_duration: number;
  word_count: number;
}

// ── Project ──────────────────────────────────
export interface VideoProject {
  id: string;
  title: string;
  prompt: string;
  style: VideoStyle;
  platform: ExportPlatform;
  script?: GeneratedScript;
  voice_model: VoiceModel;
  subtitle_style: SubtitleStyle;
  subtitle_position: SubtitlePosition;
  background_music?: string;
  effects: VideoEffects;
  status: RenderStatus;
  progress: number;
  error?: string;
  output_path?: string;
  thumbnail_path?: string;
  created_at: string;
  updated_at: string;
}

export interface VideoEffects {
  auto_zoom: boolean;
  punch_in_out: boolean;
  cinematic_transitions: boolean;
  sound_effects: boolean;
  background_blur: boolean;
  beat_sync: boolean;
  motion_graphics: boolean;
}

// ── Generation Request ───────────────────────
export interface GenerationRequest {
  prompt: string;
  style: VideoStyle;
  platform: ExportPlatform;
  voice_model: VoiceModel;
  subtitle_style: SubtitleStyle;
  subtitle_position: SubtitlePosition;
  background_music?: string;
  language: string;
  effects: VideoEffects;
  custom_script?: string;
}

// ── AI Outputs ───────────────────────────────
export interface AITitleSuggestions {
  titles: string[];
  hooks: string[];
}

export interface AIDescriptionResult {
  description: string;
  hashtags: string[];
  keywords: string[];
}

// ── Template ─────────────────────────────────
export interface VideoTemplate {
  id: string;
  name: string;
  description: string;
  style: VideoStyle;
  thumbnail: string;
  default_effects: VideoEffects;
  default_subtitle_style: SubtitleStyle;
  prompt_examples: string[];
  tags: string[];
}

// ── Queue ─────────────────────────────────────
export interface RenderJob {
  job_id: string;
  project_id: string;
  status: RenderStatus;
  progress: number;
  current_step: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

// ── UI ────────────────────────────────────────
export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
}
