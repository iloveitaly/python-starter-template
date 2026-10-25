import type { RouteConfig } from "@react-router/dev/routes"
import { index, layout, route } from "@react-router/dev/routes"

// unlike previous RR versions, loaders and other options are not available
// this is meant to be a simple way to define routes configuration at a high level

export default [
  index("routes/index.tsx"),
  layout("layouts/authenticated.tsx", [
    route("/home", "routes/home.tsx"),
    route("/form", "routes/form.tsx"),
    route("/logout", "routes/logout.tsx"),
  ]),
  layout("layouts/unauthenticated.tsx", [
    route("/login", "routes/login.tsx"),
    route("/pay", "routes/pay.tsx"),
    route("/pay/confirmation", "routes/pay-confirmation.tsx"),
  ]),
] satisfies RouteConfig
