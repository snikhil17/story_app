/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'nunito': ['Nunito', 'sans-serif'],
        'baloo': ['"Baloo 2"', 'cursive'],
        'caveat': ['Caveat', 'cursive'],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        'enchanted-teal-dark': '#1A3A3A',
        'enchanted-teal-light': '#2A4B4B',
        'ancient-gold': '#C0A068',
        'mystic-lavender': '#9B88B2',
        'cosmic-latte': '#FFF7E8',
        'brand-bg': '#F5F3FF', 
        'brand-bg-darker': '#EDE9FE',
      },
      boxShadow: {
        'book': '0 25px 50px -12px rgba(0, 0, 0, 0.35)',
        'inner-glow': 'inset 0 0 15px 0 rgba(255, 247, 232, 0.3)',
        'gold-glow': '0 0 15px 0px rgba(192, 160, 104, 0.4)',
        'magical': '0 0 20px rgba(192, 160, 104, 0.3), 0 0 40px rgba(155, 136, 178, 0.2)',
      },
      keyframes: {
        'sparkle': {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.5)', opacity: '0.5' },
        },
        'subtle-float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'fadeIn': {
          '0%': { opacity: '0', transform: 'translateY(20px) scale(0.98)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 15px 0px rgba(192, 160, 104, 0.4)' },
          '50%': { boxShadow: '0 0 25px 5px rgba(192, 160, 104, 0.6)' },
        },
        'star-twinkle': {
          '0%, 100%': { opacity: '0.7', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.2)' },
        },
        'magical-shimmer': {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '50%': { opacity: '1' },
          '100%': { transform: 'translateX(100%)', opacity: '0' },
        },
      },
      animation: {
        'sparkle': 'sparkle 2s ease-in-out infinite',
        'subtle-float': 'subtle-float 6s ease-in-out infinite',
        'fadeIn': 'fadeIn 0.8s ease-out forwards',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'star-twinkle': 'star-twinkle 3s ease-in-out infinite',
        'magical-shimmer': 'magical-shimmer 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
