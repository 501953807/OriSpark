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
        // Single cohesive accent — desaturated teal for professional feel
        primary: 'oklch(56% 0.12 170)',
        surface: 'oklch(100% 0 0)',
        bg: 'oklch(98% 0.004 240)',
        fg: 'oklch(20% 0.02 240)',
        muted: 'oklch(50% 0.018 240)',
        border: 'oklch(90% 0.006 240)',
        // Removed redundant accent2/green/blue/purple/orange — use only primary as accent
      },
      fontFamily: {
        // Display font with character + fallback hierarchy
        display: ['Söhne', 'Satoshi', 'Avenir Next', 'system-ui', 'sans-serif'],
        // Body uses Merriweather for editorial feel + sans-serif fallback
        body: ['Merriweather', 'system-ui', 'SF Pro Text', 'sans-serif'],
      },
      // More nuanced radius scale — tighter inner elements, softer containers
      borderRadius: {
        sm: '6px',        /* inner elements */
        default: '12px',  /* cards/buttons */
        lg: '16px',       /* panels */
        xl: '24px',       /* hero areas */
        pill: '9999px',   /* tags */
      },
      // Typography improvements — wider line height for readability
      lineHeight: {
        tight: '1.25',
        normal: '1.5',
        relaxed: '1.625',
      },
    },
  },
  plugins: [],
} satisfies Config
