import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
  ],
  base: '/',
  server: {
    proxy: {
      '/hackclub-api': {
        target: 'https://ai.hackclub.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/hackclub-api/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
