"""
Playwright helpers to fill out various Stripe forms.
"""

from playwright.sync_api import Page, expect


# removed old card_number version, only card_type version remains
def fill_stripe_checkout(
    page: Page,
    *,
    card_type: str = "success",  # "success" | "failure"
) -> None:
    card_number_map = {
        "success": "4242424242424242",  # Stripe test card for success
        "failure": "4000000000000002",  # Stripe test card for failure (card declined)
    }
    card_number = card_number_map.get(card_type, "4242424242424242")

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
        stripe_frame.get_by_role("button", name="Card").click()
        if stripe_frame.get_by_text("Card number").is_visible():
            break
    else:
        expect(stripe_frame.get_by_text("Card number")).to_be_visible()

    stripe_frame.get_by_role("textbox", name="Card number").click()
    stripe_frame.get_by_role("textbox", name="Card number").fill(card_number)
    stripe_frame.get_by_role("textbox", name="Expiration date MM / YY").fill("10 / 30")
    stripe_frame.get_by_role("textbox", name="Security code").fill("123")
    stripe_frame.get_by_label("Country").select_option("US")
    stripe_frame.get_by_role("textbox", name="ZIP code").fill("80110")
