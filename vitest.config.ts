import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    setupFiles: ['src/__tests__/setup.ts'],
    include: ['src/**/*.{test,spec}.ts'],
  },
  resolve: {
    alias: {
      src: fileURLToPath(new URL('./src', import.meta.url)),
      components: fileURLToPath(new URL('./src/components', import.meta.url)),
      layouts: fileURLToPath(new URL('./src/layouts', import.meta.url)),
      pages: fileURLToPath(new URL('./src/pages', import.meta.url)),
      stores: fileURLToPath(new URL('./src/stores', import.meta.url)),
      boot: fileURLToPath(new URL('./src/boot', import.meta.url)),
    },
  },
});
