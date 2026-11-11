from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.factories.clerk import get_clerk_dev_user
from app.generated.react_router_routes import react_router_url

from app.models.user import User

from tests.constants import LONG_INTEGRATION_TEST_TIMEOUT
from tests.log import log

from .clerk import setup_clerk_testing_token

# TODO scroll to bottom?
# page.evaluate("window.scrollTo(0, document.body.scrollHeight)")


def apply_playwright_timeouts(page: Page, timeout_ms: int) -> None:
    """
    CI is slower than local environments, so we need to increase the default timeouts for Playwright operations to avoid false negatives.
    """

    log.info("applying playwright timeouts", timeout_ms=timeout_ms)
    page.set_default_timeout(timeout_ms)
    page.set_default_navigation_timeout(timeout_ms)
    expect.set_options(timeout=timeout_ms)


def wait_for_loading(page: Page, timeout: int = 30_000, extreme: bool = False):
    """
    Comprehensive loading detection for React Router, TanStack Query, Clerk, and CSS animations/transitions.

    Parameters:
        page: Playwright page object
        timeout: Maximum wait time in milliseconds
        extreme: Whether to use additional React-specific and animation loading detection
    """

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_load_state("load")

    try:
        page.wait_for_load_state("networkidle")
    except PlaywrightError:
        log.info("network did not report idle")

    if extreme:
        try:
            page.wait_for_function(
                """() => {
                    // wait for clerk sdk to finish bootstrapping if it has been injected
                    if (window.Clerk && !window.Clerk.loaded) {
                        return false;
                    }

                    // wait for react router initial hydration, route navigations, revalidations, and active fetchers
                    const router = window.__reactRouterDataRouter;
                    if (router?.state) {
                        const { initialized, navigation, revalidation, fetchers } = router.state;
                        const activeFetchers =
                            fetchers instanceof Map
                                ? Array.from(fetchers.values()).some((f) => f.state !== "idle")
                                : Object.values(fetchers || {}).some((f) => f.state !== "idle");

                        if (
                            !initialized ||
                            navigation?.state !== "idle" ||
                            revalidation !== "idle" ||
                            activeFetchers
                        ) {
                            return false;
                        }
                    }

                    // wait for in-flight tanstack query fetches and mutations
                    const queryClient = window.__queryClient;
                    if (
                        queryClient &&
                        (queryClient.isFetching() > 0 || queryClient.isMutating() > 0)
                    ) {
                        return false;
                    }

                    // wait for visible loading spinners, suspense fallbacks, and aria-busy elements to unmount
                    const loadingIndicators = document.querySelectorAll(
                        '[data-suspense-fallback="true"], [aria-busy="true"], .loading-spinner, [data-loading="true"], [data-testid="loading-spinner"]'
                    );
                    if (loadingIndicators.length > 0) {
                        return false;
                    }

                    // check explicit root-level loading dataset flags if set
                    if (
                        document.documentElement.dataset.reactRouterLoading === "true" ||
                        document.documentElement.dataset.queryLoading === "true" ||
                        document.documentElement.dataset.reactTransition === "active"
                    ) {
                        return false;
                    }

                    // wait for finite css transitions/animations to settle while ignoring infinite loops like animate-spin
                    const finiteAnimations = document
                        .getAnimations()
                        .filter((anim) => anim.effect?.getTiming().iterations !== Infinity);
                    if (finiteAnimations.length > 0) {
                        return false;
                    }

                    return true;
                }""",
                timeout=timeout,
            )
        except PlaywrightTimeoutError as e:
            log.warning("react and animation loading check timed out", error=e)

    page.wait_for_timeout(100)


def login_as_dev_user(page: Page) -> User:
    username, password, _user = get_clerk_dev_user()

    # paranoid testing to ensure database cleaning is working
    assert User.count() == 0

    setup_clerk_testing_token(page)

    page.goto(react_router_url("/"))

    page.get_by_label("Email address").fill(username)
    page.get_by_role("button", name="Continue", exact=True).click()

    password_input = page.locator(
        'input[name="password"]:not([disabled]):not([aria-disabled="true"])'
    ).first
    otp_input = page.get_by_label("Enter verification code", exact=True)

    # depending on clerk configuration, clerk may prompt for password, OTP directly, or password then OTP
    password_input.or_(otp_input).first.wait_for(state="visible")

    used_password = password_input.is_visible()
    if used_password:
        password_input.fill(password)
        page.get_by_role("button", name="Continue").click()

    # depending on clerk configuration, we may need to enter OTP
    # "Enter verification code" is the aria-label and not visible on page
    try:
        if used_password:
            otp_input.wait_for(state="visible", timeout=2_500)
        else:
            otp_input.wait_for(state="visible")
        otp_input.press_sequentially(
            # slowly type the verification code, it's one single input
            "424242",
            delay=100,
        )

        # there is not button that triggers submission, it auto-submits on complete input
        # we need to ensure the loading states are reset before moving on, otherwise we won't be on the next page when
        # so we wait for the OTP field to dissapear
        otp_input.wait_for(state="detached", timeout=LONG_INTEGRATION_TEST_TIMEOUT)
    except PlaywrightTimeoutError, PlaywrightError:
        # OTP step is optional depending on clerk configuration
        log.debug("clerk OTP step skipped or timed out")

    wait_for_loading(page)

    # The wait command above is brittle and does not guarantee that the clerk login process has finished.
    # However, we know that if we've navigated away from the root URL that we properly logged into the application.
    # In order to provide a more robust loading completion indicator, we assert that the
    # current pages route is not the route that we started on. This will ensure that we've completed the login step and
    # have moved into the application.
    page.wait_for_url(
        lambda url: url != react_router_url("/"), timeout=LONG_INTEGRATION_TEST_TIMEOUT
    )

    # only a single doctor should be created!
    assert User.count() == 1

    return User.one()


def safely_scroll_then_click(locator: Locator):
    """
    If a button is off screen, the default scroll then click can sometimes
    cause the wrong thing to be clicked. I believe this has to do with the
    iframes embedded in the page, but we can't be sure.

    This was true as of version: 138.0.7204.23
    """

    locator.scroll_into_view_if_needed()
    locator.page.wait_for_timeout(1_500)
    locator.click()

    # Optionally, return locator if chaining is needed
    return locator


def safely_scroll_then_check(locator: Locator, checked: bool):
    """Same iframe-induced instability as `safely_scroll_then_click`, but for checkboxes."""

    locator.scroll_into_view_if_needed()
    locator.page.wait_for_timeout(1_500)

    if locator.is_checked() != checked:
        locator.click()

    if checked:
        expect(locator).to_be_checked()
    else:
        expect(locator).not_to_be_checked()

    return locator
