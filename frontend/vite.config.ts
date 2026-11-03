import { defineConfig } from "vite";

// Salida hacia ../public, desde donde Vercel sirve los estáticos por CDN.
// En desarrollo, /api se reenvía a uvicorn (uvicorn backend.api:app --reload).
export default defineConfig({
  build: {
    outDir: "../public",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
