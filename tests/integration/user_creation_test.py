import time

from playwright.sync_api import Page, expect

from app.models.user import User

from tests.constants import CLERK_DEV_USER_PASSWORD
from tests.integration.clerk import setup_clerk_testing_token
from tests.integration.server import home_url
from tests.integration.utils import login_as_dev_user, wait_for_loading


def test_signin(server, page: Page, assert_snapshot) -> None:
    _user = login_as_dev_user(page)

    expect(page.locator("body")).to_contain_text("Hello From Internal Python")

    assert_snapshot(page)

    assert User.count() == 1


def test_signup(server, page: Page, assert_snapshot) -> None:
    # paranoid testing to ensure database cleaning is working
    assert User.count() == 0

    setup_clerk_testing_token(page)

    unix_timestamp = int(time.time())

    page.goto(home_url())

    page.get_by_text("Sign up").click()

    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(
        f"mike-{unix_timestamp}+clerk_test@example.com"
    )
    page.get_by_label("Password", exact=True).fill(CLERK_DEV_USER_PASSWORD)
    page.get_by_role("button", name="Continue", exact=True).click()

    # wait_for_timeout is milliseconds

    page.get_by_label("Enter verification code. Digit").fill("4")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 2").fill("2")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 3").fill("4")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 4").fill("2")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 5").fill("4")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 6").fill("2")

    wait_for_loading(page)

    expect(page.locator("body")).to_contain_text("Hello From Internal Python")

    assert_snapshot(page)

    wait_for_loading(page)

    assert_snapshot(page)

    # user should be created at this point!
    assert User.count() == 1

    # logout
    page.locator(".flex > div:nth-child(3)").first.click()
    page.get_by_role("menuitem", name="Sign out").click()

    expect(page.locator("body")).to_contain_text("Sign in")

    assert_snapshot(page)
