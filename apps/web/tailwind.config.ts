import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        primary: 'var(--primary)',
        'primary-foreground': 'var(--primary-foreground)',
        secondary: 'var(--secondary)',
        'secondary-foreground': 'var(--secondary-foreground)',
        accent: 'var(--accent)',
        'accent-foreground': 'var(--accent-foreground)',
        destructive: 'var(--destructive)',
        'destructive-foreground': 'var(--destructive-foreground)',
        muted: 'var(--muted)',
        'muted-foreground': 'var(--muted-foreground)',
        border: 'var(--border)',
        input: 'var(--input)',
        ring: 'var(--ring)',
        card: 'var(--card)',
        'card-foreground': 'var(--card-foreground)',
        'frosted-blue': '#89d2dc',
        'slate-blue': '#6564db',
        granite: '#5b6c5d',
        dark: '#040403',
        light: '#ffffff',
        frosted: {
          50: '#f0fafa',
          100: '#e0f5f6',
          200: '#c1ebee',
          300: '#89d2dc',
          400: '#5bc0c0',
          500: '#4db8b8',
          600: '#26a69a',
          700: '#009688',
          800: '#00796b',
          900: '#004d40',
        },
        slatebrand: {
          50: '#f3f2ff',
          100: '#e8e7ff',
          200: '#d1cfff',
          300: '#6564db',
          400: '#5a59cc',
          500: '#4e4dbd',
          600: '#4240ae',
          700: '#36359f',
          800: '#2a2990',
          900: '#1e1d81',
        },
        graniteScale: {
          50: '#fafaf9',
          100: '#f5f5f4',
          200: '#e7e5e4',
          300: '#5b6c5d',
          400: '#4a5a4d',
          500: '#3d4d40',
          600: '#303933',
          700: '#242c26',
          800: '#181f1a',
          900: '#0d130f',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-in-out',
      },
    },
  },
  plugins: [],
}

export default config
