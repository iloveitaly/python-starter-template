import { requireEnv } from "~/utils/environment"

import * as Sentry from "@sentry/react"
import { loadStripe } from "@stripe/stripe-js"

import { log } from "./logging"

const STRIPE_PUBLISHABLE_KEY = requireEnv("VITE_STRIPE_PUBLIC_KEY")

// apiVersion cannot be set on the frontend anymore, the api version used on the backend is picked up automatically
// catch so a blocked/offline js.stripe.com fetch is not an unhandledrejection (Sentry also ignoreErrors the message)
export const stripePromise = loadStripe(STRIPE_PUBLISHABLE_KEY).catch(
  (error: unknown) => {
    log.warn("stripe.js failed to load", { error: String(error) })
    Sentry.addBreadcrumb({
      category: "stripe",
      message: "Failed to load Stripe.js",
      level: "warning",
    })
    return null
  },
)
