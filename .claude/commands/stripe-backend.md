## Stripe Backend

- `cast(object, ...)` should not be used. Can you instead cast expandable fields to PaymentIntent, or whatever their expandable type is?
- `from stripe import Charge` can we use top-level imports instead of importing from private packages?
- Do not `customer = getattr(session, "customer", None)` instead just access `session.customer` and assert that it is not null. Use the pattern for all stripe objects.
- When iterating through a list that you expect to be comprehensive use `auto_paging_iter` for example `stripe_client.prices.list(params={ ... }).auto_paging_iter()`
- Assume the new `StripeClient` is used everywhere and type it as such. When using this client, all API params should be a dictionary inside a `params=` kwarg.
- `amount_refunded=0` when the charge is disputed. The dispute amount only exists in the `balance_transactions` of the dispute object.
