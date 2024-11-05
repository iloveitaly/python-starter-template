import { defineConfig } from "vite"
import Terminal from "vite-plugin-terminal"
import tsconfigPaths from "vite-tsconfig-paths"

import { reactRouter } from "@react-router/dev/vite"
import { sentryVitePlugin } from "@sentry/vite-plugin"

export default defineConfig({
  plugins: [
    sentryVitePlugin({
      // real component names in errors
      reactComponentAnnotation: { enabled: true },
    }),
    Terminal(),
    reactRouter({ ssr: false }),
    tsconfigPaths(),
  ],
})
