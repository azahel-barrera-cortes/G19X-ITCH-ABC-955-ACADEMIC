/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Paleta verde institucional alineada con el PDF corporativo.
        corporativo: {
          50: '#e5f2f0',
          100: '#d4ebe6',
          200: '#a8d7cc',
          300: '#7cc3b2',
          400: '#50af98',
          500: '#037c5d',
          600: '#036a50',
          700: '#025540',
          800: '#023f30',
        },
        acento: {
          100: '#e5f2f0',
          400: '#037c5d',
          500: '#037c5d',
          600: '#025540',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        tarjeta: '0 1px 2px rgba(3, 124, 93, 0.06), 0 8px 24px rgba(3, 124, 93, 0.06)',
      },
    },
  },
  plugins: [],
}
