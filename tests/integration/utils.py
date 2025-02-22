from playwright.sync_api import Page

from app.models.user import User

from tests.integration.clerk import setup_clerk_testing_token
from tests.integration.server import home_url
from tests.routes.utils import get_clerk_dev_user


def login_as_dev_user(page: Page):
    username, password, user = get_clerk_dev_user()

    # paranoid testing to ensure database cleaning is working
    assert User.count() == 0

    setup_clerk_testing_token(page)

    page.goto(home_url())

    page.get_by_label("Email address").fill(username)
    page.get_by_role("button", name="Continue", exact=True).click()

    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Continue").click()

    page.wait_for_load_state("networkidle")

    # only a single doctor should be created!
    assert User.count() == 1

    return User.first()
