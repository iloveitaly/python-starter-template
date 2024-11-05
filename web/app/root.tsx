import { Links, Meta, Outlet, Scripts, ScrollRestoration } from "react-router"
import type { LinksFunction } from "react-router"

import "~/app.css"
import withChakraProvider from "~/configuration/chakra"
import withClerkProvider from "~/configuration/clerk"
import withPostHogProvider from "~/configuration/posthog"
import withSentryProvider from "~/configuration/sentry"

export const links: LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
  },
]

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  )
}

function App() {
  return <Outlet />
}

// TODO(mbianco) figure out type issue here + move to config index
function applyProviders(
  app: () => React.ComponentType,
  providers: ((app: React.ComponentType) => JSX.Element)[],
) {
  return providers.reduce((acc, provider) => provider(acc), app)
}

export default applyProviders(App, [
  withChakraProvider,
  withPostHogProvider,
  // withClerkProvider,
  withSentryProvider,
])
