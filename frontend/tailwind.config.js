/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Paleta institucional alineada con el PDF corporativo (azul jurídico + dorado).
        corporativo: {
          50: '#f2f6fb',
          100: '#e2eaf6',
          200: '#c4d5ec',
          300: '#9bb6da',
          400: '#6b8fc0',
          500: '#1f4e79',
          600: '#1a4164',
          700: '#12213a',
          800: '#0d1a2d',
        },
        acento: {
          100: '#f7efdc',
          400: '#d3a84a',
          500: '#b98a2f',
          600: '#96701f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        tarjeta: '0 1px 2px rgba(15, 32, 58, 0.06), 0 8px 24px rgba(15, 32, 58, 0.06)',
      },
    },
  },
  plugins: [],
}
