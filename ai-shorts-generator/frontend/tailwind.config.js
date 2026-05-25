/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // ── Base dark palette ──────────────────────
        background: {
          DEFAULT: '#080810',
          secondary: '#0f0f1a',
          tertiary: '#161625',
          card: '#1a1a2e',
          hover: '#1f1f35',
        },
        border: {
          DEFAULT: '#2a2a45',
          light: '#353560',
        },
        // ── Neon accents ───────────────────────────
        neon: {
          purple: '#a855f7',
          blue: '#3b82f6',
          cyan: '#06b6d4',
          pink: '#ec4899',
          green: '#10b981',
        },
        // ── Text ──────────────────────────────────
        text: {
          primary: '#f1f0ff',
          secondary: '#9898c0',
          muted: '#5a5a80',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'neon-glow':
          'linear-gradient(135deg, #a855f720 0%, #3b82f620 50%, #06b6d420 100%)',
        'card-gradient':
          'linear-gradient(145deg, #1a1a2e 0%, #161625 100%)',
      },
      boxShadow: {
        'neon-purple': '0 0 20px #a855f740, 0 0 40px #a855f720',
        'neon-blue': '0 0 20px #3b82f640, 0 0 40px #3b82f620',
        'neon-cyan': '0 0 20px #06b6d440, 0 0 40px #06b6d420',
        card: '0 4px 24px rgba(0,0,0,0.4)',
        'card-hover': '0 8px 32px rgba(0,0,0,0.6)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        shimmer: 'shimmer 2s linear infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        glowPulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
