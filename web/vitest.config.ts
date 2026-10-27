/// <reference types="vitest" />
/// <reference types="vite/client" />
import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"

export default defineConfig({
  plugins: [react()],
  resolve: {
    tsconfigPaths: true,
  },
  test: {
    globals: true,
    environment: "happy-dom",
    environmentOptions: {
      happyDOM: {
        settings: {
          disableJavaScriptFileLoading: true,
        },
      },
    },
    setupFiles: ["./test/setup-test-env.ts"],
    coverage: {
      provider: "v8",
    },
  },
})
