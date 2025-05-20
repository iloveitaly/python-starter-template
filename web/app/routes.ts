import type { RouteConfig } from "@react-router/dev/routes"
import { index, layout, route } from "@react-router/dev/routes"

// unlike previous RR versions, loaders and other options are not available
// this is meant to be a simple way to define routes configuration at a high level

export default [
  index("routes/index.tsx"),
  layout("layouts/authenticated.tsx", [
    route("/home", "routes/home.tsx"),
    route("/form", "routes/form.tsx"),
  ]),
] satisfies RouteConfig
