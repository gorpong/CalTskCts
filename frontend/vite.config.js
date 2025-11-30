import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    // Output to Flask's static directory
    outDir: '../src/caltskcts/static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        // Predictable file names for Flask
        entryFileNames: 'js/[name].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith('.css')) {
            return 'css/[name][extname]'
          }
          return 'assets/[name]-[hash][extname]'
        }
      }
    }
  },
  server: {
    // Proxy API calls to Flask during development
    proxy: {
      '/contacts': 'http://localhost:5000',
      '/events': 'http://localhost:5000',
      '/tasks': 'http://localhost:5000'
    }
  }
})
