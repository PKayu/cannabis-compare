import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cannabis: {
          50: '#f5fdf0',
          100: '#e8fae2',
          200: '#d0f4c9',
          300: '#a9e9a6',
          400: '#7bd97f',
          500: '#52c952',
          600: '#39a636',
          700: '#2d7f2d',
          800: '#265326',
          900: '#1f4620',
        },
      },
    },
  },
  plugins: [],
}

export default config
