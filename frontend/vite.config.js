import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El proxy de desarrollo evita problemas de CORS: las peticiones a /api se
// reenvían al backend de FastAPI (por defecto en el puerto 8000).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
