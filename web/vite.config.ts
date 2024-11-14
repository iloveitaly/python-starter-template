import { reactRouterDevTools } from "react-router-devtools"
import { defineConfig } from "vite"
import { loadEnv } from "vite"
import Terminal from "vite-plugin-terminal"
import tsconfigPaths from "vite-tsconfig-paths"

import { reactRouter } from "@react-router/dev/vite"
import { sentryVitePlugin } from "@sentry/vite-plugin"

// ensure that the env variables are loaded if they are used!
function requireEnvCheckerPlugin(mode: string) {
  const env = loadEnv(mode, process.cwd())

  return {
    name: "vite-plugin-require-env-checker",
    enforce: "pre",
    transform(code: string, id: string) {
      // Only check JS/TS files
      if (!/\.(js|ts|jsx|tsx)$/.test(id)) return

      const requireEnvRegex = /requireEnv\(["'`](.*?)["'`]\)/g
      let match
      const missingVars = new Set()

      while ((match = requireEnvRegex.exec(code)) !== null) {
        const envKey = match[1]
        if (!env[envKey]) {
          missingVars.add(envKey)
        }
      }

      if (missingVars.size > 0) {
        const missingVarsList = Array.from(missingVars).join(", ")
        throw new Error(
          `Missing environment variables for requireEnv: ${missingVarsList}`,
        )
      }
    },
  }
}

function getModePlugins(mode: string) {
  if (mode === "production") {
    return [
      sentryVitePlugin({
        // real component names in errors
        reactComponentAnnotation: { enabled: true },
      }),
    ]
  }

  return [Terminal(), reactRouterDevTools()]
}
export default defineConfig(({ mode }) => ({
  plugins: [
    ...getModePlugins(mode),
    requireEnvCheckerPlugin(mode),
    reactRouter({ ssr: false }),
    tsconfigPaths(),
  ],
}))
