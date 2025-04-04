from playwright.sync_api import Page

from app.models.user import User

from tests.integration.clerk import setup_clerk_testing_token
from tests.integration.server import home_url
from tests.routes.utils import get_clerk_dev_user

# TODO scroll to bottom?
# page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

# set_timeout
# page.set_default_timeout(120_000)
# page.set_default_navigation_timeout(120_000)


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
            from app import log

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

    wait_for_loading(page)

    # only a single doctor should be created!
    assert User.count() == 1

    return User.first()
