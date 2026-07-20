import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['tests/sandbox/**/*.test.js'],
    testTimeout: 10000,
  },
});
