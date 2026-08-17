/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Tauri expects a fixed port for its dev server proxy: `src-tauri/tauri.conf.json`
// `build.devUrl` points at http://localhost:1420, so this must not drift.
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
  },
  test: {
    environment: 'jsdom',
  },
})
