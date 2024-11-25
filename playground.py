#!/usr/bin/env -S ipython -i
# isort: off

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


def delete_all_users():
	clerk.users.list()
		| fp.pluck_attr("id")
		| fp.lmap(lambda uid: clerk.users.delete(user_id=uid))
