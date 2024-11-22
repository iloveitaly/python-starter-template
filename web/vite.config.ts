import { defineConfig } from "vite"
import { loadEnv } from "vite"
import Terminal from "vite-plugin-terminal"
import tsconfigPaths from "vite-tsconfig-paths"

import { reactRouter } from "@react-router/dev/vite"
import { sentryVitePlugin } from "@sentry/vite-plugin"

// TODO extract out to another file
// ensure that the env variables are loaded if they are used!
function requireEnvCheckerPlugin(mode: string) {
  const env = loadEnv(mode, process.cwd())

  return {
    name: "vite-plugin-require-env-checker",
    enforce: "pre",
    transform(code: string, id: string) {
      // Only check JS/TS files
      if (!/\.(js|ts|jsx|tsx)$/.test(id)) return

      // TODO make the method name that is checked for configurable
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
    const authToken = process.env.SENTRY_AUTH_TOKEN

    // fine for sentry to have auth under a CI build being used for integration testing
    if (!authToken) {
      const VITE_BUILD_COMMIT = process.env.VITE_BUILD_COMMIT
      const CI = process.env.CI

      // if build is dirty, then we aren't building for prod (probably local)
      // ensuring dirty builds are not deployed is checked upstream
      // if we are in CI, then it's fine not to have a sentry token
      // remember, although production builds are created in CI, they are done within
      // a docker container and do not inherit CI and other ENV vars

      if (!CI && !VITE_BUILD_COMMIT.endsWith("-dirty")) {
        throw new Error("Missing SENTRY_AUTH_TOKEN. Include to fix build.")
      }

      console.warn("Missing SENTRY_AUTH_TOKEN. Sentry will not be enabled.")
    }

    return [
      // Put the Sentry vite plugin after all other plugins
      authToken &&
        sentryVitePlugin({
          // real component names in errors
          reactComponentAnnotation: { enabled: true },
          //    org: process.env.SENTRY_ORG,
          // project: process.env.SENTRY_PROJECT,

          // Auth tokens can be obtained from https://sentry.io/orgredirect/organizations/:orgslug/settings/auth-tokens/
          // authToken: process.env.SENTRY_AUTH_TOKEN,
        }),
      // only check env vars when building for production
      // some ENV is only available in prod
      requireEnvCheckerPlugin(mode),
    ]
  }

  return [
    Terminal(),
    // TODO this is still tool beta for rr7, need to wait for a more stable release
    // reactRouterDevTools()
  ]
}

function getBuildConfig(_mode: string) {
  return {
    // TODO maybe use envDir to point to a fake directory
    // base url where JS assets are served out of
    // base: mode === "development" ? "/" : "/assets/",
  }
}

// test configuration is done via vitest.config.ts, this is only for the build system
export default defineConfig(({ mode }) => ({
  // TODO need to disable .env file loading https://discord.com/channels/804011606160703521/1307442221288656906
  ...getBuildConfig(mode),
  // build.outDir is ignored and buildDirectory in react-router.config.ts is used instead
  server: {
    // by default, vite will only listen on ipv6 loopback!
    // there does not seem to be an easy way to listen on ipv4 & ipv6
    // https://caddy.community/t/reverse-proxy-only-looking-to-ipv4-loopback/26345
    host: "0.0.0.0",
    // if the port is in use, fail loudly
    strictPort: true,
    // random ports to avoid conflict with other projects
    port: parseInt(process.env.JAVASCRIPT_SERVER_PORT),
  },
  plugins: [reactRouter(), tsconfigPaths(), ...getModePlugins(mode)],
}))
