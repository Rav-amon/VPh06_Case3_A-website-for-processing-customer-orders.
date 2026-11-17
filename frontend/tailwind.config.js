/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0b0907',
          900: '#14110e',
          800: '#1f1a15',
          700: '#2c241c',
        },
        gold: {
          100: '#f4ead0',
          200: '#e8d5a3',
          300: '#d4b56a',
          400: '#c9a962',
          500: '#b8923f',
        },
        mist: '#cfc6b8',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans: ['"Outfit"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 24px 60px rgba(0, 0, 0, 0.35)',
      },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translateY(18px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        drift: {
          '0%, 100%': { transform: 'translate3d(0, 0, 0) scale(1)' },
          '50%': { transform: 'translate3d(18px, -28px, 0) scale(1.08)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '100% 50%' },
        },
      },
      animation: {
        rise: 'rise 0.8s ease-out both',
        drift: 'drift 16s ease-in-out infinite',
        shimmer: 'shimmer 8s linear infinite',
      },
    },
  },
  plugins: [],
};
