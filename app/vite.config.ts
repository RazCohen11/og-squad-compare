import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Relative base so the build also works from a GitHub Pages sub-path (D27)
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    // Never inline flag SVGs as data URLs: there are ~270 of them and only a few are shown per game
    assetsInlineLimit: (filePath) => (filePath.includes('flag-icons') ? false : undefined),
  },
})
