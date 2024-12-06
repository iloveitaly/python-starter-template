#!/usr/bin/env -S uv run ipython -i

# isort: off

from pydantic import BaseModel, field_validator, model_validator
import sqlmodel as sm
import sqlalchemy as sa

from sqlmodel import SQLModel, Session, select
from app.configuration.clerk import clerk
from app.configuration.database import database_url
from app.models import *
from activemodel.session_manager import get_session
from app.models import llm_response
from app.models.llm_response import LLMResponse
from app.models.user import User
from activemodel.session_manager import get_engine

def inspect_environment():
    """Display relevant custom functions and variables with minimal formatting"""
    import inspect
    from typing import get_type_hints
    from rich.console import Console
    from rich.text import Text
    from pathlib import Path

    console = Console()
    width = console.width
    current_module = inspect.currentframe().f_globals
    ipython_path = Path.home() / ".ipython"
    builtin_modules = {'os', 'sys', 'json', 'tempfile', 'subprocess', 'importlib', 'pkgutil'}
    ipy_modules = {'IPython', 'ipykernel'}
    exclude_vars = {'In', 'Out', 'PIPE', 'get_ipython', 'exit', 'quit', 'c'}

    def truncate_text(text: str, max_width: int) -> str:
        if len(text) > max_width:
            return text[:max_width-3] + "..."
        return text

    def get_module_info(module) -> str:
        module_path = getattr(module, '__path__', [''])[0]
        version = getattr(module, '__version__', 'unknown version')
        return f"{module.__name__} ({version}) from {module_path}"

    # Functions Section
    console.print("\n[bold blue]Custom Functions[/bold blue]")
    console.print("─" * width)

    for name, obj in current_module.items():
        if (inspect.isfunction(obj) and
            not name.startswith('_') and
            obj.__module__ == '__main__'):
            # Get the source file of the function
            try:
                source_file = Path(inspect.getfile(obj))
                # Skip if function is from .ipython directory
                if ipython_path in source_file.parents:
                    continue
            except (TypeError, ValueError):
                continue

            sig = str(inspect.signature(obj))
            return_type = get_type_hints(obj).get('return', None)
            if return_type:
                sig += f" -> {return_type.__name__}"
            text = Text()
            text.append(f"{name:<30}", style="cyan bold")
            text.append(truncate_text(sig, width-30), style="green")
            console.print(text)

    # Modules Section
    console.print("\n[bold blue]Imported Modules[/bold blue]")
    console.print("─" * width)

    for name, obj in current_module.items():
        if (inspect.ismodule(obj) and
            not name.startswith('_') and
            name not in builtin_modules and
            name not in exclude_vars):
            text = Text()
            text.append(f"{name:<30}", style="cyan bold")
            text.append(truncate_text(get_module_info(obj), width-30), style="yellow")
            console.print(text)

    # Variables Section
    console.print("\n[bold blue]Variables[/bold blue]")
    console.print("─" * width)

    for name, obj in current_module.items():
        if (not inspect.isfunction(obj) and
            not inspect.ismodule(obj) and
            not inspect.isclass(obj) and
            not name.startswith('_') and
            name not in builtin_modules and
            name not in exclude_vars):
            type_info = type(obj).__name__
            if hasattr(obj, '__annotations__'):
                annotations = getattr(obj, '__annotations__', {})
                if annotations:
                    type_info += f" [{', '.join(str(v) for v in annotations.values())}]"
            text = Text()
            text.append(f"{name:<30}", style="cyan bold")
            text.append(truncate_text(type_info, width-30), style="green")
            console.print(text)


# TODO not sure if this works
def patch_reload():
	# Store the original reload function
	_original_reload = importlib.reload

	def custom_reload(module):
		"""
		Custom reload function that wraps importlib.reload and resets
		SQLModel metadata after reloading the module.
		"""
		log.info("Clearing metadata before reload...")
		SQLModel.metadata.clear()

		result = _original_reload(module)
		return result

	# Replace the original reload with the custom one
	importlib.reload = custom_reload

patch_reload()

async def playwright_page():
	"""
	>>> page = await playwright_page()
	>>> response = await page.goto("https://www.google.com")
	>>> response.status
	"""

	from playwright.async_api import async_playwright

	playwright = await async_playwright().start()
	browser = await playwright.chromium.launch(headless = True)
	page = await browser.new_page()
	return page

def create_user():
	clerk.users.create({"email_address": "test@test.com"})

import funcy_pipe as fp

def delete_all_users():
	clerk.users.list() | fp.filter(lambda user: user.email_addresses[0].email_address != "mike+clerk_test@example.com") | fp.pluck_attr("id") | fp.lmap(lambda uid: clerk.users.delete(user_id=uid))


from sqlmodel import create_engine
import os

engine = create_engine(database_url(), echo=True)

from redis import Redis

def get_db_version() -> tuple[str, str]:
	with engine.connect() as conn:
		pg_version = conn.execute(sa.text("SHOW server_version")).scalar()
		# Extract major.minor version from full version string
		pg_version = pg_version.split()[0]

	return pg_version

def get_redis_version(redis_url: str):
	# Get Redis version
	redis_client = Redis.from_url(redis_url)
	redis_version = redis_client.info()['redis_version']

	return redis_version

# with Session(get_engine()) as session:
# 	user = User(clerk_id="hi")
# 	llm_response = LLMResponse(
# 		model="gpt-3.5-turbo",
# 		category="test",
# 		prompt="hello",
# 		response="world",
# 		prompt_hash="hi"
# 	)
# 	session.add(llm_response)
# 	session.add(user)
# 	session.commit()
# 	# session.close()

# llm_response = LLMResponse(
# 	model="gpt-3.5-turbo",
# 	category="test",
# 	prompt="hello from save",
# 	response="world",
# )
# llm_response.save()

# from activemodel import BaseModel as ActiveModelBaseModel
# from pydantic import validate_model

# # TODO this approach isn't great, it model_validate copies the entire model when successful
# class TestSQLModelValidationWithConstructor(ActiveModelBaseModel):
#     def __init__(self, **data) -> None:
#         super().__init__(**data)
#         _, _, validation_error = self.__class__.model_validate(self.__class__, data)
#         if validation_error:
#             raise validation_error

#     @model_validator(mode="before")
#     @classmethod
#     def before_validation(cls, data):
#          breakpoint()

# class TestValidationModel(BaseModel):
#     prompt: str
#     prompt_hash: str | None

#     @model_validator(mode="before")
#     @classmethod
#     def check_card_number_omitted(cls, data):
#         if isinstance(data, dict):
#             assert "card_number" not in data, "card_number should not be included"
#         return data

#     @field_validator("prompt_hash")
#     @classmethod
#     def prevent_explicit_hash(cls, v):
#         if v is not None:
#             raise ValueError("prompt_hash cannot be set explicitly")
#         return v

# # TestValidationModel(prompt="foo", prompt_hash="bar")

# Call it whenever needed
inspect_environment()
