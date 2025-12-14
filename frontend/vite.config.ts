import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'recharts': ['recharts'],
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // Only proxy /admin API endpoints, not the page itself
      '^/admin/(?!$)': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
