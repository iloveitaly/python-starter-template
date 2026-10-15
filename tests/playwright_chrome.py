import os

import pytest


def use_docker_chrome(config: pytest.Config) -> bool:
    "Compose chromium is the default renderer. A visible window stays on the host browser."

    if config.getoption("--headed"):
        return False

    # PWDEBUG opens the inspector against a local browser window
    if os.environ.get("PWDEBUG") in {"1", "console"}:
        return False

    return bool(os.environ.get("PLAYWRIGHT_CHROME_WS_ENDPOINT"))
