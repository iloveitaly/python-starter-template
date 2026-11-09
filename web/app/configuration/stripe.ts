import { requireEnv } from "~/utils/environment"

import { loadStripe } from "@stripe/stripe-js"

const STRIPE_PUBLISHABLE_KEY = requireEnv("VITE_STRIPE_PUBLIC_KEY")

// apiVersion cannot be set on the frontend anymore, the api version used on the backend is picked up automatically
export const stripePromise = loadStripe(STRIPE_PUBLISHABLE_KEY)
