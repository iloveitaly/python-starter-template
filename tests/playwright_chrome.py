import os

import pytest

from app.env import loose_env


def use_docker_chrome(config: pytest.Config) -> bool:
    "Compose chromium is the default renderer. A visible window stays on the host browser."

    if config.getoption("--headed"):
        return False

    # PWDEBUG opens the inspector against a local browser window
    if os.environ.get("PWDEBUG") in {"1", "console"}:
        return False

    return bool(loose_env.str("PLAYWRIGHT_CHROME_WS_ENDPOINT"))
