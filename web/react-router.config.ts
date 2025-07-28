import type { Config } from "@react-router/dev/config"
import { sentryOnBuildEnd } from "@sentry/react-router"

// TODO is mode passed over here at all? So we can avoid the NODE_ENV reference?

export default {
  ssr: false,
  buildDirectory: "build/" + process.env.NODE_ENV,
  // required by sentry documentation https://docs.sentry.io/platforms/javascript/guides/react-router/
  buildEnd: async ({ viteConfig, reactRouterConfig, buildManifest }) => {
    if (viteConfig.mode === "production") {
      await sentryOnBuildEnd({ viteConfig, reactRouterConfig, buildManifest })
    }
  },
  // TODO list routes out you want to prerender here for SEO + caching purposes
  // async prerender() {
  //   return ["/"]
  // },
} satisfies Config
