import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{vue,ts,tsx,js,jsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: 'oklch(98% 0.004 240)',
        surface: 'oklch(100% 0 0)',
        fg: 'oklch(20% 0.02 240)',
        muted: 'oklch(50% 0.018 240)',
        border: 'oklch(90% 0.006 240)',
        accent: 'oklch(56% 0.12 170)',
        accent2: 'oklch(62% 0.16 280)',
        grad1: 'oklch(56% 0.12 170)',
        grad2: 'oklch(62% 0.16 260)',
        green: 'oklch(56% 0.12 170)',
        orange: 'oklch(62% 0.18 55)',
        blue: 'oklch(58% 0.14 245)',
        purple: 'oklch(58% 0.16 280)',
        pink: 'oklch(58% 0.16 350)',
      },
      fontFamily: {
        display: ['Söhne', 'Avenir Next', 'system-ui', 'sans-serif'],
        body: ['system-ui', 'SF Pro Text', 'sans-serif'],
      },
      borderRadius: {
        sm: '8px',
        DEFAULT: '14px',
        lg: '20px',
        xl: '28px',
      },
    },
  },
  plugins: [],
} satisfies Config
