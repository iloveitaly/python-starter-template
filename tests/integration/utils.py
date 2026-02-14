from math import floor

from playwright.sync_api import Locator, Page, expect

from app import log

from app.models.user import User

from tests.constants import LONG_INTEGRATION_TEST_TIMEOUT
from tests.routes.utils import get_clerk_dev_user

from .clerk import setup_clerk_testing_token
from .server import home_url

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


def wait_for_loading(page: Page, timeout: int = 30000, extreme: bool = False):
    """
    Comprehensive loading detection for modern React 18+ applications, including CSS animations/transitions.

    Parameters:
        page: Playwright page object
        timeout: Maximum wait time in milliseconds
        extreme: Whether to use additional React-specific and animation loading detection
    """
    # Basic page loading states
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_load_state("load")
    page.wait_for_load_state("networkidle")

    # Add React-specific and animation detection when extreme=True
    if extreme:
        page.evaluate("""() => {
            window._reactLoadingComplete = false;

            const checkLoadingComplete = async () => {
                try {
                    // 1. Check for React Suspense fallbacks (React 18+)
                    const suspenseFallbacks = document.querySelectorAll('[data-suspense-fallback="true"]');
                    if (suspenseFallbacks.length > 0) return false;

                    // 2. Check React Router 6+ navigation state
                    if (window.document.documentElement.dataset.reactRouterLoading === 'true') return false;

                    // 3. Check for TanStack Query/React Query loading state
                    if (document.documentElement.dataset.queryLoading === 'true') return false;

                    // 4. Check for common loading indicators
                    const loadingIndicators = document.querySelectorAll(
                        '[aria-busy="true"], .loading-spinner, [data-loading="true"]'
                    );
                    if (loadingIndicators.length > 0) return false;

                    // 5. Wait for any React transitions to complete (React 18+)
                    if (document.documentElement.dataset.reactTransition === 'active') return false;

                    // 6. Wait for CSS animations and transitions to finish
                    const animations = document.getAnimations();
                    if (animations.length > 0) return false;

                    return true;
                } catch (e) {
                    console.error("Error in loading detection:", e);
                    return true; // Prevent hanging on error
                }
            };

            // Poll until loading is complete or timeout occurs
            const startTime = Date.now();
            const poll = async () => {
                if (await checkLoadingComplete()) {
                    window._reactLoadingComplete = true;
                } else if (Date.now() - startTime > 10000) {
                    // Timeout after 10 seconds of polling
                    console.warn("React and animation loading detection timed out");
                    window._reactLoadingComplete = true;
                } else {
                    setTimeout(poll, 100);
                }
            };

            poll();
        }""")

        # Wait for React and animation loading to complete
        try:
            page.wait_for_function(
                "() => window._reactLoadingComplete === true", timeout=timeout
            )
        except Exception as e:
            log.warning(f"React and animation loading check timed out: {e}")

    # Brief pause for any final renders
    page.wait_for_timeout(100)


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

    # depending on clerk configuration, we may need to enter OTP
    # "Enter verification code" is the aria-label and not visible on page
    otp_input = page.get_by_label("Enter verification code", exact=True)
    try:
        otp_input.wait_for(state="visible", timeout=2_500)
        otp_input.press_sequentially(
            # slowly type the verification code, it's one single input
            "424242",
            delay=100,
        )

        # there is not button that triggers submission, it auto-submits on complete input
        # we need to ensure the loading states are reset before moving on, otherwise we won't be on the next page when
        # so we wait for the OTP field to dissapear
        otp_input.wait_for(state="detached", timeout=LONG_INTEGRATION_TEST_TIMEOUT)
    except Exception:
        # TODO we should have a more scoped exception here
        pass

    wait_for_loading(page)

    # The wait command above is brittle and does not guarantee that the clerk login process has finished.
    # However, we know that if we've navigated away from the root URL that we properly logged into the application.
    # In order to provide a more robust loading completion indicator, we assert that the
    # current pages route is not the route that we started on. This will ensure that we've completed the login step and
    # have moved into the application.
    page.wait_for_url(
        lambda url: url != home_url(), timeout=LONG_INTEGRATION_TEST_TIMEOUT
    )

    # only a single doctor should be created!
    assert User.count() == 1

    return User.first()


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
