/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  safelist: [
    { pattern: /^(bg|text|border|ring|shadow)-(accent|success|warning|danger)/ },
    'bg-accent',
    'bg-accent-hover',
    'hover:bg-accent-hover',
    'focus:border-accent',
    'focus:ring-accent',
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#09090b',
          secondary: '#111113',
          tertiary: '#18181b',
          card: '#18181b',
          hover: '#27272a',
        },
        border: {
          DEFAULT: '#27272a',
          light: '#3f3f46',
        },
        accent: {
          DEFAULT: '#6366f1',
          hover: '#818cf8',
        },
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
        text: {
          primary: '#fafafa',
          secondary: '#a1a1aa',
          muted: '#52525b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.5)',
        accent: '0 0 0 2px #6366f130',
      },
      animation: {
        shimmer: 'shimmer 2s linear infinite',
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
