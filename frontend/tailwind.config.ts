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
        // Remapped to 70s groovy palette — low range = warm amber, high range = action teal
        cannabis: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#0D9488',
          700: '#0F766E',
          800: '#115E59',
          900: '#134E4A',
        },
        groovy: {
          amber: '#F97316',
          teal: '#0D9488',
          cobalt: '#2563EB',
          cream: '#FFF8EE',
          dark: '#134E4A',
          ink: '#1C1917',
          sun: '#FCD34D',
          rust: '#C2410C',
        },
      },
      fontFamily: {
        display: ['var(--font-fredoka)', 'sans-serif'],
        body: ['var(--font-nunito)', 'sans-serif'],
        sans: ['var(--font-nunito)', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        sticker: '4px 4px 0px #1C1917',
        'sticker-lg': '6px 6px 0px #1C1917',
        'sticker-amber': '4px 4px 0px #F97316',
        'sticker-teal': '4px 4px 0px #0D9488',
      },
      borderRadius: {
        groovy: '1.25rem',
      },
    },
  },
  plugins: [],
}

export default config
