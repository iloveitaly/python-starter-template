"""
Main entrypoint to the server of the application.

- nixpacks triggers a python build when a main.py is present, do not change the name of this file.
- when running fastapi in dev mode, it adds PWD to PYTHONPATH. In production, this is not the case, which is why we need to do it ourselves here
- the __name__ guard ensures that `fastapi dev` can still consume this file and `python main.py` is only executed in production
- fastapi's cli tooling is in a separate repo. We've modeled our uvicorn invocation after theirs.
  https://github.com/fastapi/fastapi-cli/blob/9a4741816dc288bbd931e693166117d98ee14dea/src/fastapi_cli/cli.py#L162-L171
"""

import os
import sys

sys.path.append(os.path.dirname(__file__))

from app.server import api_app

if __name__ == "__main__":
    import uvicorn
    from decouple import config

    PORT = config("PORT", cast=int)

    uvicorn.run(
        api_app,
        # bind on all interfaces in production
        host="0.0.0.0",
        port=PORT,
        # TODO we should tune this and have it pulled from env
        # workers=2,
        # NOTE important to ensure structlog controls logging in production
        log_config=None,
    )
