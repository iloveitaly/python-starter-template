"""
Playwright helpers to fill out various Stripe forms.
"""

from playwright.sync_api import Page


def fill_stripe_checkout(page: Page) -> None:
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

    stripe_frame.get_by_role("button", name="Card").click()
    stripe_frame.get_by_role("textbox", name="Card number").click()
    stripe_frame.get_by_role("textbox", name="Card number").fill("4242 4242 4242 4242")
    stripe_frame.get_by_role("textbox", name="Expiration date MM / YY").fill("10 / 30")
    stripe_frame.get_by_role("textbox", name="Security code").fill("123")
    stripe_frame.get_by_label("Country").select_option("US")
    stripe_frame.get_by_role("textbox", name="ZIP code").fill("80110")
