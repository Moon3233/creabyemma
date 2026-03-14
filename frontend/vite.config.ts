import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/ws': { target: 'http://127.0.0.1:8000', ws: true },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/login': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/logout': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/upload': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/update_vetement_name': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/delete_vetement_image': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
