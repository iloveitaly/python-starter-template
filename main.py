"""
Main entrypoint to the uvicorn server

Some notes:

- Railpack triggers a python build when a main.py is present, do not change the name of this file.
- When running fastapi in dev mode, it adds PWD to PYTHONPATH. In production, this is not the case.
- The __name__ guard ensures that `fastapi dev` can still consume this file and `python main.py` is only executed in production
- Fastapi's cli tooling is in a separate repo. We've modeled our uvicorn invocation after theirs.
  https://github.com/fastapi/fastapi-cl i/blob/9a4741816dc288bbd931e693166117d98ee14dea/src/fastapi_cli/cli.py#L162-L171
- Customizing which files are watched for autoreload is challenging (no excludes). https://github.com/fastapi/fastapi/discussions/2863
- The integration tests also run a server. If we make major updates here, we need to manually adjust that command.
- Some deployments set a PORT variable, some only set it on the Procfile (dokku when using a non-web process type).
"""


def get_server_config():
    from app.env import env

    from app.environments import is_development

    additional_args = {}

    if is_development():
        additional_args = {
            "reload": True,
            "reload_excludes": [
                # git + venv are automatically excluded
                "web/node_modules/*",
                "tmp/*",
                "web/*",
                "tests/*",
            ],
        }

    PORT = env.int("PORT")

    # TODO we should tune this and have it pulled from env
    # workers=2,

    config_args = {
        # a import path is required for dev, so we use that for prod as well
        "app": "app.server:api_app",
        # bind on all interfaces
        "host": "0.0.0.0",
        "port": PORT,
        # NOTE important to ensure structlog controls logging in production
        "log_config": None,
        # a custom access logger is implemted which plays nicely with structlog
        "access_log": False,
        # loop="auto" is default, which looks like anyio in a stacktrace, but anyio uses uvloop behind the scenes
        # workers=None is default, which looks at WEB_CONCURRENCY to determine the workers to use
        **additional_args,
    }

    return config_args


def check_fastapi_cli():
    import fastapi_cli.cli

    from app import log
    from app.utils.patching import hash_function_code

    if (
        hash_function_code(fastapi_cli.cli._run)
        != "d7e4dad43fc556d58b699fdf316eba558b75ece0d73f177176578c2ee8745f3b"
    ):
        log.warning("fastapi-cli internal _run function has changed, update main.py")


# uvicorn will "rerun" this file in some way, so although we should be able to throw an exception when this condition
# isn't met that ends up causing issues with how uvicorn is invoked.
if __name__ == "__main__":
    import uvicorn

    check_fastapi_cli()

    uvicorn.run(**get_server_config())
