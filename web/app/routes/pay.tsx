import { useEffect, useRef, useState } from "react"
import { href, useNavigate } from "react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type { StripeCheckoutElementsSdk } from "@stripe/stripe-js"

import { AllMeta } from "~/components/shared/AllMeta"
import { ServerErrorAlert } from "~/components/shared/ServerErrorAlert"
import { Button } from "~/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "~/components/ui/form"
import { Input } from "~/components/ui/input"
import { Skeleton } from "~/components/ui/skeleton"
import {
  createExamplePaymentPending,
  createExamplePaymentSession,
  publicClient,
  publicClientLoader,
} from "~/configuration/client"
import { log } from "~/configuration/logging"
import { stripePromise } from "~/configuration/stripe"
import { formatCurrency } from "~/lib/currency"

import { zodResolver } from "@hookform/resolvers/zod"
import { invariant } from "@epic-web/invariant"

import type { Route } from "./+types/pay"

const formSchema = z.object({
  email: z.email("Enter a valid email"),
})

function messageFromApiError(error: unknown) {
  if (
    error &&
    typeof error === "object" &&
    "error" in error &&
    error.error &&
    typeof error.error === "object" &&
    "message" in error.error &&
    typeof error.error.message === "string"
  ) {
    return error.error.message
  }

  return "Payment could not be completed. Refresh the page and try again."
}

export async function clientLoader(_loaderArgs: Route.ClientLoaderArgs) {
  const { data } = await createExamplePaymentSession({
    client: publicClientLoader,
  })

  if (!data) {
    throw new Response("Server Error", { status: 500 })
  }

  return data
}

export default function ExamplePaymentPage({
  loaderData,
}: Route.ComponentProps) {
  const navigate = useNavigate()
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { email: "" },
  })
  const checkoutRef = useRef<StripeCheckoutElementsSdk | null>(null)
  const billingMountRef = useRef<HTMLDivElement>(null)
  const paymentMountRef = useRef<HTMLDivElement>(null)


  const [checkoutReady, setCheckoutReady] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function mountCheckout() {
      const stripe = await stripePromise
      invariant(stripe, "Stripe.js failed to load")

      if (cancelled || !billingMountRef.current || !paymentMountRef.current) {
        return
      }

      // Checkout Elements SDK reads the API version from this client secret
      const checkout = stripe.initCheckoutElementsSdk({
        clientSecret: loaderData.client_secret,
      })
      const billingElement = checkout.createBillingAddressElement()
      const paymentElement = checkout.createPaymentElement({
        fields: { billingDetails: { address: "never" } },
      })

      if (cancelled) {
        return
      }

      billingElement.mount(billingMountRef.current)
      paymentElement.mount(paymentMountRef.current)
      checkoutRef.current = checkout
      setCheckoutReady(true)
    }

    void mountCheckout()

    return () => {
      cancelled = true
      checkoutRef.current?.getBillingAddressElement()?.unmount()
      checkoutRef.current?.getPaymentElement()?.unmount()
      checkoutRef.current = null
    }
  }, [loaderData.client_secret])

  const {
    formState: { isSubmitting, errors },
    setError,
    clearErrors,
  } = form

  const amountLabel =
    loaderData.currency === "usd"
      ? formatCurrency(loaderData.amount_cents)
      : `${loaderData.amount_cents} ${loaderData.currency}`

  async function onSubmit(values: z.infer<typeof formSchema>) {
    clearErrors("root")

    const checkout = checkoutRef.current
    invariant(checkout, "Checkout is not ready")

    const loaded = await checkout.loadActions()
    if (loaded.type === "error") {
      setError("root.serverError", { message: loaded.error.message })
      return
    }

    const pending = await createExamplePaymentPending({
      client: publicClient,
      body: { client_secret: loaderData.client_secret },
    })

    if (pending.error || !pending.data) {
      log.info("example payment pending rejected", {
        message: messageFromApiError(pending.error),
      })
      setError("root.serverError", {
        message: messageFromApiError(pending.error),
      })
      return
    }

    const confirmed = await loaded.actions.confirm({
      email: values.email,
      redirect: "if_required",
    })

    if (confirmed.type === "error") {
      setError("root.serverError", { message: confirmed.error.message })
      return
    }

    const sessionId = pending.data.stripe_checkout_session_id
    navigate(
      `${href("/pay/confirmation")}?session_id=${encodeURIComponent(sessionId)}`,
    )
  }

  return (
    <div className="mx-auto mt-10 max-w-md px-4">
      <AllMeta
        basic={{
          title: "Example payment",
          description: "Pay with Stripe Checkout to exercise the payment helpers.",
        }}
      />
      <h1 className="mb-2 text-2xl font-bold">Example payment</h1>
      <p className="text-muted-foreground mb-6">
        {loaderData.product_name} · {amountLabel}. Use test card 4242 4242 4242
        4242, any future expiry, and any CVC.
      </p>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input type="email" autoComplete="email" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div>
            <p className="mb-2 text-sm font-medium">Billing address</p>
            <div ref={billingMountRef} />
          </div>
          <div>
            <p className="mb-2 text-sm font-medium">Card</p>
            <div ref={paymentMountRef} />
            {!checkoutReady && <Skeleton className="h-40 w-full" />}
          </div>
          <ServerErrorAlert error={errors.root?.serverError} />
          <Button
            type="submit"
            className="w-full"
            disabled={!checkoutReady || isSubmitting}
          >
            {isSubmitting ? "Paying..." : `Pay ${amountLabel}`}
          </Button>
        </form>
      </Form>
    </div>
  )
}
