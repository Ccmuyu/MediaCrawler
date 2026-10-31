import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Cyberpunk color scheme using CSS variables
        cyber: {
          // Background colors
          bg: {
            primary: 'rgb(var(--cyber-bg-primary) / <alpha-value>)',
            secondary: 'rgb(var(--cyber-bg-secondary) / <alpha-value>)',
            tertiary: 'rgb(var(--cyber-bg-tertiary) / <alpha-value>)',
            panel: 'rgb(var(--cyber-bg-panel) / <alpha-value>)',
            elevated: 'rgb(var(--cyber-bg-elevated) / <alpha-value>)',
            glass: 'rgb(var(--glass-bg))',
            glassDark: 'rgb(var(--glass-dark-bg))',
          },
          // Neon colors
          neon: {
            cyan: 'rgb(var(--cyber-neon-cyan) / <alpha-value>)',
            cyanDim: 'rgb(var(--cyber-neon-cyan-dim) / <alpha-value>)',
            pink: 'rgb(var(--cyber-neon-pink) / <alpha-value>)',
            pinkDim: 'rgb(var(--cyber-neon-pink-dim) / <alpha-value>)',
            green: 'rgb(var(--cyber-neon-green) / <alpha-value>)',
            greenDim: 'rgb(var(--cyber-neon-green-dim) / <alpha-value>)',
            orange: 'rgb(var(--cyber-neon-orange) / <alpha-value>)',
            yellow: 'rgb(var(--cyber-neon-yellow) / <alpha-value>)',
            purple: 'rgb(var(--cyber-neon-purple) / <alpha-value>)',
          },
          // Text colors
          text: {
            primary: 'rgb(var(--cyber-text-primary) / <alpha-value>)',
            secondary: 'rgb(var(--cyber-text-secondary) / <alpha-value>)',
            muted: 'rgb(var(--cyber-text-muted) / <alpha-value>)',
          },
          // Border colors
          border: {
            DEFAULT: 'rgb(var(--cyber-border-default) / <alpha-value>)',
            glow: 'rgb(var(--cyber-border-glow) / <alpha-value>)',
            subtle: 'rgb(var(--cyber-border-subtle) / <alpha-value>)',
          },
        },
        // Keep semantic colors for compatibility
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      fontFamily: {
        sans: ['"Noto Sans SC"', 'PingFang SC', 'Microsoft YaHei', 'system-ui', 'sans-serif'],
        serif: ['"Noto Serif SC"', 'Songti SC', 'SimSun', 'Georgia', 'serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 1px 2px rgba(28, 25, 23, 0.06)',
        'glow-cyan-sm': '0 1px 2px rgba(28, 25, 23, 0.05)',
        'glow-pink': '0 1px 2px rgba(28, 25, 23, 0.06)',
        'glow-pink-sm': '0 1px 2px rgba(28, 25, 23, 0.05)',
        'glow-green': '0 1px 2px rgba(28, 25, 23, 0.06)',
        'glow-green-sm': '0 1px 2px rgba(28, 25, 23, 0.05)',
        'glow-orange': '0 1px 2px rgba(28, 25, 23, 0.06)',
        'cyber-card': '0 1px 2px rgba(28, 25, 23, 0.04), 0 10px 28px rgba(28, 25, 23, 0.05)',
        'cyber-inset': 'inset 0 1px 0 rgba(255, 255, 255, 0.04)',
        'cyber-soft': '0 1px 2px rgba(28, 25, 23, 0.05)',
        'cyber-float': '0 12px 32px rgba(28, 25, 23, 0.08)',
        'cyber-elevated': '0 18px 48px rgba(28, 25, 23, 0.1)',
      },
      animation: {
        'slide-up': 'slideUp 0.3s ease-out forwards',
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'scanline': 'scanline 8s linear infinite',
        'cursor-blink': 'cursorBlink 1s step-end infinite',
        'border-glow': 'borderGlow 3s linear infinite',
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
      keyframes: {
        slideUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': {
            boxShadow: '0 0 5px rgb(var(--cyber-neon-cyan) / 0.5), 0 0 10px rgb(var(--cyber-neon-cyan) / 0.3)'
          },
          '50%': {
            boxShadow: '0 0 15px rgb(var(--cyber-neon-cyan) / 0.8), 0 0 25px rgb(var(--cyber-neon-cyan) / 0.5), 0 0 35px rgb(var(--cyber-neon-cyan) / 0.3)'
          },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        cursorBlink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        borderGlow: {
          '0%, 100%': { borderColor: 'rgb(var(--cyber-neon-cyan) / 0.3)' },
          '50%': { borderColor: 'rgb(var(--cyber-neon-cyan) / 0.6)' },
        },
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
