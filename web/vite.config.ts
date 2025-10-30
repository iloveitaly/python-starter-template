import { reactRouterDevTools } from "react-router-devtools"
import { type ConfigEnv, type PluginOption, defineConfig } from "vite"
import { checkEnv } from "vite-plugin-check-env"
import viteCompression from "vite-plugin-compression"
import devtoolsJson from "vite-plugin-devtools-json"
import svgr from "vite-plugin-svgr"
import Terminal from "vite-plugin-terminal"
import tsconfigPaths from "vite-tsconfig-paths"

import { invariant } from "@epic-web/invariant"
import { reactRouter } from "@react-router/dev/vite"
import { sentryReactRouter } from "@sentry/react-router"
import tailwindcss from "@tailwindcss/vite"

const JAVASCRIPT_SERVER_PORT = process.env.JAVASCRIPT_SERVER_PORT

function getModePlugins(config: ConfigEnv): PluginOption[] {
  // when `typegen` is run, the import.meta.* vars are not set
  // additionally, typegen runs `react-router build` under the hood, which sets the mode to production by default
  // however, what we are trying to detect here is when the application is being built for production
  const viteAndNodeAreProduction =
    config.mode === "production" && process.env.NODE_ENV === "production"

  if (viteAndNodeAreProduction) {
    const SENTRY_AUTH_TOKEN = process.env.SENTRY_AUTH_TOKEN
    const VITE_BUILD_COMMIT = process.env.VITE_BUILD_COMMIT

    // fine for sentry to have auth under a CI build being used for integration testing
    if (!SENTRY_AUTH_TOKEN) {
      const CI = process.env.CI

      if (!VITE_BUILD_COMMIT) {
        throw new Error(
          "Missing VITE_BUILD_COMMIT environment variable. Include to run production build.",
        )
      }

      // If build is dirty, then we aren't building for prod (probably local)
      // ensuring dirty builds are not deployed is checked upstream via Justfiles, so we can rely on this.
      //
      // If we are in CI, then it's fine not to have a sentry token.
      //
      // Remember, although production builds are created in CI, they are done within
      // a docker container and do not inherit CI and other ENV vars, so although it's built in a CI environment
      // the CI environment variables are not set, which is what we are concerned about here.

      if (!CI && !VITE_BUILD_COMMIT.endsWith("-dirty")) {
        throw new Error("Missing SENTRY_AUTH_TOKEN. Include to fix build.")
      }

      console.warn("Missing SENTRY_AUTH_TOKEN. Sentry will not be enabled.")
    }

    return [
      // only check env vars when building for production, some ENV are only available in prod
      checkEnv(),
      viteCompression(),

      // Put the Sentry vite plugin after all other plugins
      SENTRY_AUTH_TOKEN &&
        sentryReactRouter(
          {
            // real component names in errors
            reactComponentAnnotation: { enabled: true },

            // TODO unsure if this is required
            org: process.env.SENTRY_ORG,
            project: process.env.SENTRY_PROJECT,

            // Auth tokens can be obtained from https://ORG_NAME.sentry.io/settings/auth-tokens/new-token/
            authToken: process.env.SENTRY_AUTH_TOKEN,

            release: {
              name: VITE_BUILD_COMMIT,
            },
          },
          config,
        ),
    ].filter((item) => item !== undefined && item !== null && item !== "")
  }

  // this will fail when building prod, so we have to force when we are building dev
  invariant(
    JAVASCRIPT_SERVER_PORT,
    "Missing JAVASCRIPT_SERVER_PORT environment variable. Include to run build.",
  )

  return [Terminal(), devtoolsJson()]
}

// test configuration is done via vitest.config.ts, this is only for the build system
export default defineConfig((config) => ({
  // TODO need to disable .env file loading https://discord.com/channels/804011606160703521/1307442221288656906
  // build.outDir is ignored and buildDirectory in react-router.config.ts is used instead
  build: {
    // option required for Sentry sourcemap upload
    sourcemap: true,
  },
  // annoying to have to worry about removing these, and we don't have our standard logging
  // https://github.com/vitejs/vite/discussions/7920
  esbuild: {
    drop: ["console", "debugger"],
  },
  server: {
    // by default, vite will only listen on ipv6 loopback!
    // there does not seem to be an easy way to listen on ipv4 & ipv6
    // https://caddy.community/t/reverse-proxy-only-looking-to-ipv4-loopback/26345
    host: "0.0.0.0",
    // if the port is in use, fail loudly
    strictPort: true,
    // use the same port every time so localias is happy
    port: parseInt(JAVASCRIPT_SERVER_PORT),
  },
  plugins: [
    // needs to go first, and needs to be conditional!
    config.mode === "development" && reactRouterDevTools(),
    tailwindcss(),
    reactRouter(),
    tsconfigPaths(),
    // `?react` to end of SVG imports to transform to React components
    svgr(),
    ...getModePlugins(config),
  ],
}))
