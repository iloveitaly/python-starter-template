## Dev In Browser

Use your browser to view `https://verso.localhost` which is tied to livereload dev server which is already running. You can inspect that page (including taking screenshots!) to validate that your changes fixed the issue.

If the site does not load, stop your work and let me know.

## Fastapi_Stripe

A Stripe Checkout implementation takes four steps:

1. Create a checkout session. Happens when the user visits the checkout page.
2. Create a pending order. Happens right before the user is sent to Stripe.
3. Complete the order. Happens when the user is redirected back to the app after payment.
4. Check the order status. Happens when the user visits the confirmation page, which could happen multiple times.

Here's an example implementation:

```python
from .configuration import stripe_client, origin_url

@screening_api_app.post("/")
def create_order_session(
    request: Request,
) -> str:
    """
    Creates a checkout session. This happens after the user visits
    the checkout page.
    """
    session = stripe_client.v1.checkout.sessions.create(
        params={
            "ui_mode": "custom",
            "line_items": [
                {
                    "price": "price_123",
                    "quantity": 1,
                }
            ],
            "mode": "payment",
            # CHECKOUT_SESSION_ID is a placeholder for the actual session id, which is replaced by Stripe
            # cannot use include_query_params because the Stripe checkout template variable is escaped
            "return_url": (
                # `request` required for abs URL generation
                str(request.url_for("complete_ticket_purchase"))
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
        }
    )

    return session.client_secret


class PendingOrderRequest(BaseModel):
    stripe_checkout_session_id: str

    email: str
    # and other fields...


@screening_api_app.post("/pending")
def create_pending_order(
    data: PendingOrderRequest,
    distribution: Distribution = Depends(get_distribution_by_host),
) -> TypeIDType:
    """
    Right before we pass off the user to Stripe, we save all order information.

    This can happen multiple times if there is a form submission error with Stripe.

    This pending step is in place largely because many payment methods require a redirect to a confirmation page,
    so we assume we'll always be redirected.

    The database schema ensures duplicate stripe checkout session ids never happen.
    """


    # let's validate the stripe checkout session id is real
    stripe_session = stripe_client.v1.checkout.sessions.retrieve(
        data.stripe_checkout_session_id
    )

    if stripe_session.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your checkout session has expired. Please refresh the page and try again.",
        )

    order = Order.one_or_none(
        stripe_checkout_session_id=data.stripe_checkout_session_id
    )

    if order:
        order.email = data.email
        # ...and other fields...
        order.save()
    else:
        order = Order(
            stripe_checkout_session_id=data.stripe_checkout_session_id,
            email=data.email,
        ).save()

    return order.id


@screening_api_app.get("/complete")
def complete_ticket_purchase(
    request: Request,
    session_id: str = Query(),
):
    stripe_session = stripe_client.v1.checkout.sessions.retrieve(session_id)

    if stripe_session.status != "complete":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    order = Order.one(stripe_checkout_session_id=session_id)

    order.status = OrderState.paid
    order.save()

    redirect_url = f"{origin_url}/screening/{order.screening_id}/confirmation/{session_id}"
    return RedirectResponse(url=redirect_url)


@screening_api_app.get("/confirmation")
def ticket_purchase_status(
    request: Request,
    stripe_checkout_session_id: str = Query(),
    screening_id: TypeIDType = Query(),
) -> str:
    stripe_client = distribution.stripe_client()
    stripe_session = stripe_client.v1.checkout.sessions.retrieve(
        stripe_checkout_session_id
    )

    if stripe_session.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkout is not complete",
        )

    order = Order.one(stripe_checkout_session_id=stripe_checkout_session_id)
    return order.id


public_api_app.include_router(screening_api_app)
```

## Fix Tests

Focus on all unit + command tests (`pytest --exclude tests/integration`). Make sure they pass and fix errors. If you run into anything very odd: stop, and let me know. Mutate test code first and let me know if you think you should update application code.

Then, focus on integration tests in tests/integration. If an integration test fails, run it again just to be sure it wasn't a flakey test (integration tests are not deterministic). If it fails because of a visual error, check the 'tmp/test-results/playwright/' directory for a screenshot relating to the failing test that you can inspect.

For additional debugging help, view the development version of the site at `$PYTHON_TEST_SERVER_HOST` using a browser.

Do not attempt to perform this task in a sandbox. Service connections require access to host networking.

If you get stuck or seem to be in a loop, give me a short summary of exactly where you are running into trouble, let me know, and stop working.

Do not attempt to solve these issues:

* `just`, `direnv`, and `js_build` should always run or exist.
* Chromium/Chrome/playwright not working properly.
* Postgres, Redis, or other service connection errors.

If you run into errors, stop immediately and let me know with a summary of the problem.

## Implement Fastapi Routes

The file docstring contains a description of the FastAPI routes we need to implement. Implement these routes.

Avoid implementing any Stripe logic right now. I will do that later. Leave TODOs for this and other areas where you are very unsure of what to do.

## Plan Only

As this point, I only want to talk about the plan. How would you do this? What would you refactor to make this design clean? You are an expert software engineer and I want you to think hard about how to plan this project out.

Do not worry about writing database migrations. You make any changes directly to app/models/ files.

Let's separate this into key sections:

1. Refactor
2. Data model
3. Utilities/helpers/lib
4. Routes

## Python Command

- we don't have to put everything in a single perform. You can use helper functions. Can you modularize the code a bit and use helper functions so it's easier to read?

## React Router Client Loader

Do this in a `clientLoader` and use `loaderData` to render the component. DO NOT create mock data, new interfaces, or mock data loader functions. Instead, assume `loaderData` has all of the data you need to render the component.

## Refactor On Instructions

Refactor this code following all the established coding rules. Pay very careful attention to each rule and instruction and update the referenced code.

## Secrets

Here's how environment variables are managed in this application:

- `.envrc` entry point to load the correct env stack. Should not contain secrets and should be simple some shell logic and direnv stdlib calls.
- `env/all.sh` common configuration for all systems. No secrets. No dotenv/custom scripts. Just `export`s to modify core configuration settings like `export TZ=UTC`.
- `env/all.local.sh` overrides across all environments (dev and test). Useful for things like 1Password service account token and database hosts which mutate the logic followed in `env/not_production.sh`. Not committed to source control.
- `env/not_production.sh` This contains the bulk of your system configuration. Shared across test, CI, dev, etc but not production.
- `env/dev.local.sh` configuration overrides for non-test environments. `PYTHONBREAKPOINT`, `LOG_LEVEL`, etc. Most of your environment changes end up happening here.
- `env/test.sh` test-only environment variables (`PYTHON_ENV=test`). This file should generally be short.
- `env/production.{backend,frontend}.sh` for most medium-sized projects you'll have separate frontend and backend systems (even if your frontend is SPA, which I'm a fan of). These two files enable you to document the variables required to build (in the case of a SPA frontend) or run (in the case of a python backend) your system in production.
- `env/*local.*` files have a `-example` variant which is committed to version control. These document helpful environment variables for local development.
- When writing TypeScript/JavaScript/React, use `requireEnv("THE_ENV_VAR_NAME")` to read an environment variable. `import {requireEnv} from '~/utils/environment'`

## Standalone Python Scripts

# Writing Standalone Python Scripts

Use this header:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
```

- Specify dependencies via the `dependencies` variable in the above comment
- Do not install packages with pip or any other package manager, assume packages will be installed when needed
- Use `click` for CLI interfaces
- Use `structlog_config` for logging. Read the usage guide: @https://github.com/iloveitaly/structlog-config/

## Stripe Backend

- `cast(object, ...)` should not be used. Can you instead cast expandable fields to PaymentIntent, or whatever their expandable type is?
- `from stripe import Charge` can we use top-level imports instead of importing from private packages?
- Do not `customer = getattr(session, "customer", None)` instead just access `session.customer` and assert that it is not null. Use the pattern for all stripe objects.
- When iterating through a list that you expect to be comprehensive use `auto_paging_iter` for example `stripe_client.prices.list(params={ ... }).auto_paging_iter()`
- Assume the new `StripeClient` is used everywhere and type it as such. When using this client, all API params should be a dictionary inside a `params=` kwarg.
- `amount_refunded=0` when the charge is disputed. The dispute amount only exists in the `balance_transactions` of the dispute object.

## Typescript Docstring

Add a file-level docstring with a simple description of what this file does and where this is used.

