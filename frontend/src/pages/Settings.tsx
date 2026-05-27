import { Settings as SettingsIcon, Key, Cpu, Palette, Info } from 'lucide-react';

const SECTIONS = [
  {
    id: 'api',
    icon: Key,
    title: 'API Keys',
    fields: [
      { key: 'OPENAI_API_KEY', label: 'OpenAI API Key', type: 'password', placeholder: 'sk-...' },
      { key: 'PEXELS_API_KEY', label: 'Pexels API Key', type: 'password', placeholder: 'Pexels key for stock video' },
      { key: 'ELEVENLABS_API_KEY', label: 'ElevenLabs API Key', type: 'password', placeholder: 'Optional — for premium voices' },
    ],
  },
  {
    id: 'render',
    icon: Cpu,
    title: 'Rendering',
    fields: [
      { key: 'GPU_ACCELERATION', label: 'GPU Acceleration', type: 'toggle', placeholder: '' },
      { key: 'MAX_CONCURRENT_RENDERS', label: 'Max Concurrent Renders', type: 'number', placeholder: '2' },
      { key: 'DEFAULT_FPS', label: 'Default FPS', type: 'number', placeholder: '30' },
    ],
  },
  {
    id: 'style',
    icon: Palette,
    title: 'Defaults',
    fields: [
      { key: 'DEFAULT_VOICE', label: 'Default Voice Model', type: 'select', options: ['openai', 'elevenlabs', 'local'], placeholder: '' },
      { key: 'DEFAULT_SUBTITLE_STYLE', label: 'Default Subtitle Style', type: 'select', options: ['hormozi', 'tiktok', 'clean', 'fire', 'minimal', 'emoji'], placeholder: '' },
      { key: 'DEFAULT_LANGUAGE', label: 'Default Language', type: 'text', placeholder: 'en' },
    ],
  },
] as const;

export default function Settings() {
  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <SettingsIcon className="w-6 h-6 text-neon-purple" />
        <h1 className="text-2xl font-display font-bold">Settings</h1>
      </div>

      {/* Info banner */}
      <div className="card p-4 flex gap-3 border-neon-blue/30 bg-neon-blue/5">
        <Info className="w-4 h-4 text-neon-blue shrink-0 mt-0.5" />
        <p className="text-sm text-text-secondary">
          Settings are stored server-side via environment variables. Edit{' '}
          <code className="text-neon-cyan text-xs">.env</code> and restart the
          backend to apply permanent changes.
        </p>
      </div>

      {SECTIONS.map((section) => {
        const Icon = section.icon;
        return (
          <div key={section.id} className="card p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2 mb-1">
              <Icon className="w-4 h-4 text-neon-purple" />
              <h2 className="font-display font-semibold">{section.title}</h2>
            </div>

            {section.fields.map((field) => (
              <div key={field.key} className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-secondary">
                  {field.label}
                </label>
                {'options' in field ? (
                  <select className="input text-sm">
                    {field.options.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                ) : field.type === 'toggle' ? (
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-5 rounded-full bg-background-tertiary border border-border cursor-pointer relative">
                      <div className="absolute left-0.5 top-0.5 w-4 h-4 rounded-full bg-text-muted transition-transform" />
                    </div>
                    <span className="text-xs text-text-muted">Disabled</span>
                  </div>
                ) : (
                  <input
                    type={field.type}
                    className="input text-sm"
                    placeholder={field.placeholder}
                  />
                )}
              </div>
            ))}
          </div>
        );
      })}

      <div className="text-xs text-text-muted text-center">
        AI Shorts Generator v1.0.0
      </div>
    </div>
  );
}
