import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    // Output to Flask's static folder
    outDir: '../src/caltskcts/static',
    emptyOutDir: true,
  },
  server: {
    // Proxy API calls to Flask during development
    proxy: {
      '/contacts': 'http://127.0.0.1:5000',
      '/events': 'http://127.0.0.1:5000',
      '/tasks': 'http://127.0.0.1:5000',
    }
  }
})
