import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
    // Development build settings for better debugging
    minify: mode === 'production' ? 'esbuild' : false,
    sourcemap: mode === 'development' ? 'inline' : false,
    rollupOptions: {
      output: {
        manualChunks: mode === 'production' ? {
          'recharts': ['recharts'],
        } : undefined,
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
        changeOrigin: true,
      },
      '^/admin/(?!$)': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
}))
