import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// El proxy de desarrollo evita problemas de CORS: las peticiones a /api se
// reenvían al backend de FastAPI de la instancia oficial de desarrollo.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY || 'http://127.0.0.1:8001',
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
  }
})
