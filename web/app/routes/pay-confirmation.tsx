import { AllMeta } from "~/components/shared/AllMeta"
import { examplePaymentStatus, publicClientLoader } from "~/configuration/client"
import { formatCurrency } from "~/lib/currency"
import { getQueryParam } from "~/lib/utils"

import type { Route } from "./+types/pay-confirmation"

export async function clientLoader(loaderArgs: Route.ClientLoaderArgs) {
  const sessionId = getQueryParam(loaderArgs.request, "session_id")
  if (!sessionId) {
    throw new Response("Not Found", { status: 404 })
  }

  const { data } = await examplePaymentStatus({
    client: publicClientLoader,
    query: { session_id: sessionId },
  })

  if (!data) {
    throw new Response("Server Error", { status: 500 })
  }

  return data
}

export default function ExamplePaymentConfirmationPage({
  loaderData,
}: Route.ComponentProps) {
  const amountLabel =
    loaderData.currency === "usd"
      ? formatCurrency(loaderData.amount_cents)
      : `${loaderData.amount_cents} ${loaderData.currency}`
  const country = loaderData.country ?? "not collected"
  const postalCode = loaderData.postal_code ?? "not collected"

  return (
    <div className="mx-auto mt-10 max-w-md px-4">
      <AllMeta
        basic={{
          title: "Payment complete",
          description: "Example Stripe payment confirmation.",
        }}
      />
      <h1 className="mb-2 text-2xl font-bold">Payment complete</h1>
      <p className="mb-6">{amountLabel}</p>
      <dl className="space-y-2 text-sm">
        <div>
          <dt className="text-muted-foreground">Country</dt>
          <dd>{country}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Postal code</dt>
          <dd>{postalCode}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Checkout session</dt>
          <dd className="font-mono">{loaderData.stripe_checkout_session_id}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Payment intent</dt>
          <dd className="font-mono">{loaderData.payment_intent_id}</dd>
        </div>
      </dl>
      {loaderData.disputed && (
        <p className="mt-6">This payment has an active dispute.</p>
      )}
      {!loaderData.disputed && (
        <p className="mt-6">No dispute on this payment.</p>
      )}
    </div>
  )
}
