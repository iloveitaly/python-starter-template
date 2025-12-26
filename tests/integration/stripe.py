"""
Playwright helpers to fill out various Stripe forms.
"""

from typing import Any

from playwright.sync_api import Page, expect

from tests.integration.utils import safely_scroll_then_click


# removed old card_number version, only card_type version remains
def fill_stripe_checkout(
    page: Page,
    *,
    card_type: str = "success",
    only_card_number: bool = False,
) -> None:
    card_number_map = {
        "success": "4242424242424242",  # Stripe test card for success
        "failure": "4000000000000002",  # Stripe test card for failure (card declined)
    }

    card_number = card_number_map[card_type]

    # Find the Stripe iframe dynamically by its name pattern
    stripe_iframe = None
    for iframe in page.query_selector_all("iframe"):
        name = iframe.get_attribute("name")
        if name and name.startswith("__privateStripeFrame"):
            stripe_iframe = iframe
            break

    assert stripe_iframe is not None, "Stripe iframe not found"
    stripe_frame = stripe_iframe.content_frame()
    assert stripe_frame

    # had issues where the click on this button did not properly go through
    # wait_for_loading(page)

    stripe_iframe.scroll_into_view_if_needed()

    # I had a lot of issues getting this part of the page to properly click, which is why
    # we have this insane workaround
    for _ in range(3):
        # checking for this first allows us to use this method twice if we are filling out a form with
        # the intention of failing the first time, and then succeeding the second time
        if stripe_frame.get_by_text("Card number").is_visible():
            break

        safely_scroll_then_click(stripe_frame.get_by_role("button", name="Card"))
    else:
        expect(stripe_frame.get_by_text("Card number")).to_be_visible()

    stripe_frame.get_by_role("textbox", name="Card number").clear()
    stripe_frame.get_by_role("textbox", name="Card number").fill(card_number)

    if not only_card_number:
        # this field in particular has some weird keyboard hijacking that causes issues when attempting to be refilled
        stripe_frame.get_by_role("textbox", name="Expiration date MM / YY").fill(
            "10 / 30"
        )
        stripe_frame.get_by_role("textbox", name="Security code").fill("123")
        stripe_frame.get_by_label("Country").select_option("US")
        stripe_frame.get_by_role("textbox", name="ZIP code").fill("80110")

    # after these inputs are in place, a annoying link input comes up
    # this can cause issues with the next step, so we need to wait until it is visible
    # however, looks like stripe is A/B testing text on the area, so I'm matching against a TOS line :/
    expect(stripe_frame.get_by_text("Terms and Privacy Policy")).to_be_visible()

    # wait a bit, for good measure
    page.wait_for_timeout(500)


def assert_customer_attached_to_session(stripe_client: Any, session_id: str) -> None:
    """Assert that a non-guest Stripe customer is attached to the checkout session.

    - Asserts the session has a `customer` attached
    - Asserts the attached customer has an email (indicates non-guest customer)
    """
    session = stripe_client.v1.checkout.sessions.retrieve(session_id)

    assert session.customer, (
        f"expected checkout session {session_id} to have an attached customer"
    )

    customer = stripe_client.customers.retrieve(session.customer)

    assert customer.email, (
        f"expected customer {session.customer} on session {session_id} to have an email"
    )
