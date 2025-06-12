/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup/setup.ts',
    exclude: ['**/node_modules/**', '**/dist/**'],
    include: ['./src/tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}']
  }
})