import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "node:path";

// The side panel is one extension page (dist/sidepanel.html) referenced by the
// manifest. Assets are emitted relative to it so chrome-extension:// URLs resolve.
// content.js and background.js are intentionally NOT part of this bundle: they run
// in the page / service-worker contexts and must stay framework-free.
const projectRoot = import.meta.dirname;
const uiRoot = resolve(projectRoot, "src/ui");

export default defineConfig({
  root: uiRoot,
  plugins: [vue(), tailwindcss()],
  base: "./",
  build: {
    outDir: resolve(projectRoot, "dist"),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(uiRoot, "sidepanel.html"),
    },
    target: "chrome124",
  },
});
