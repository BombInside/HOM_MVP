import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  // 🚀 Ускоряет production-билд + снижает риск «Broken pipe»
  build: {
    sourcemap: false,         // отключаем тяжёлые карты
    target: "es2017",         // быстрее для bundler
    chunkSizeWarningLimit: 1600, 
    outDir: "dist",
    emptyOutDir: true
  },

  // Если используешь API на backend через /api
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
