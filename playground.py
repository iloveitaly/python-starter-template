#!/usr/bin/env -S uv run ipython -i

# isort: off

import sqlmodel as sm
import sqlalchemy as sa

from sqlmodel import Session, select
from app.models import *
from activemodel.session_manager import get_session
from app.models import llm_response
from app.models.llm_response import LLMResponse
from app.models.user import User
from activemodel.session_manager import get_engine

async def playwright_page():
	"""
	response = await page.goto("https://www.google.com")
	response.status
	"""

	from playwright.async_api import async_playwright

	playwright = await async_playwright().start()
	browser = await playwright.chromium.launch(headless = True)
	page = await browser.new_page()
	return page


# def delete_all_users():
# 	clerk.users.list()
# 		| fp.pluck_attr("id")
# 		| fp.lmap(lambda uid: clerk.users.delete(user_id=uid))


from sqlmodel import create_engine
import os

engine = create_engine(os.environ["DATABASE_URL"], echo=True)

with Session(get_engine()) as session:
	user = User(clerk_id="hi")
	llm_response = LLMResponse(
		model="gpt-3.5-turbo",
		category="test",
		prompt="hello",
		response="world",
		prompt_hash="hi"
	)
	session.add(llm_response)
	session.add(user)
	session.commit()
	# session.close()

llm_response = LLMResponse(
	model="gpt-3.5-turbo",
	category="test",
	prompt="hello from save",
	response="world",
	prompt_hash="hi"
)
llm_response.save()