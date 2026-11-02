from playwright.sync_api import Page, expect
from pytest import FixtureRequest
from pytest_playwright_artifacts import assert_no_console_errors

from app.generated.react_router_routes import react_router_url
from app.models.example_payment_order import (
    ExamplePaymentOrder,
    ExamplePaymentOrderStatus,
)

from .stripe import fill_stripe_payment_elements
from .utils import safely_scroll_then_click


def test_example_payment_completes_checkout(
    server,
    faker,
    page: Page,
    assert_snapshot,
    request: FixtureRequest,
) -> None:
    test_email = faker.email()

    # 1) Open the payment page and wait until Stripe has mounted
    page.goto(react_router_url("/pay"))

    pay_button = page.get_by_role("button", name="Pay $5.00")
    expect(pay_button).to_be_enabled()
    # Stripe iframes change height between loads, so the snapshot is the stable page intro
    assert_snapshot(page.locator(".payment-intro"), name="01-payment-form")

    # 2) Save a pending order and pay with a Stripe test card
    page.get_by_label("Email").fill(test_email)
    fill_stripe_payment_elements(page)
    safely_scroll_then_click(pay_button)

    expect(page.get_by_text("Payment complete")).to_be_visible()
    expect(page.get_by_text("US", exact=True)).to_be_visible()
    expect(page.get_by_text("80110")).to_be_visible()
    assert_snapshot(
        page,
        name="02-payment-complete",
        mask_elements=["iframe", ".font-mono", ".snapshot-mask"],
    )

    # 3) The complete route marks the pending order paid
    assert ExamplePaymentOrder.count() == 1
    order = ExamplePaymentOrder.one(email=test_email)
    assert order.status == ExamplePaymentOrderStatus.paid
    assert order.amount_cents == 5_00
    assert order.stripe_checkout_session_id.startswith("cs_")

    assert_no_console_errors(
        request,
        ignore=[
            # not_production.sh uses placeholder Sentry and PostHog keys
            "Invalid Sentry Dsn: frontend-dsn",
            {
                "file": r"https://us-assets\.i\.posthog\.com/.*",
                "message": "the server responded with a status of 404",
            },
        ],
    )
