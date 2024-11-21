import type { RouteConfig } from "@react-router/dev/routes"
import { index, layout, route } from "@react-router/dev/routes"

// unlike previous RR versions, loaders and other options are not available
// this is meant to be a simple way to define routes configuration at a high level

export default [
  index("routes/login.tsx"),
  layout("layouts/authenticated.tsx", [route("/home", "routes/home.tsx")]),
] satisfies RouteConfig
