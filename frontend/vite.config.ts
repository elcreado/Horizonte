import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;
          if (/[/\\](recharts|recharts-scale|d3-[^/\\]+|victory-vendor|lodash|decimal\.js-light|react-smooth)[/\\]/.test(id)) return 'charts';
          return 'vendor';
        },
      },
    },
  },
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
});
