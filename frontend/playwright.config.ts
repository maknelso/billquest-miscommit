import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './src/tests/e2e',
  timeout: 60000,  // Increased timeout to 60 seconds
  testMatch: '**/*.{spec,test}.{js,ts,mjs,cjs}',
  outputDir: 'test-results',  // Directory for test artifacts
  use: {
    headless: false,
    viewport: { width: 1280, height: 720 },
    video: 'retain-on-failure',  // Always keep videos on failure
    trace: 'retain-on-failure',  // Always keep traces on failure
    actionTimeout: 30000,  // Increased action timeout
    navigationTimeout: 30000,  // Increased navigation timeout
    screenshot: 'on',  // Take screenshots on failure
  },
});