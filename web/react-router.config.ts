import type { Config } from "@react-router/dev/config"

// TODO is mode passed over here at all?

export default {
  ssr: false,
  buildDirectory: "build/" + process.env.NODE_ENV,
} satisfies Config
