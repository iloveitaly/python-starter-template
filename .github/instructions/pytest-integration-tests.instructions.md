---
applyTo: "tests/integration/**/*.py"
---
## Pytest Integration Tests

- Look to tests/factories.py to generate any required database state
  - Here's an example of how to create + persist a factory `DistributionFactory.build(domain=PYTHON_TEST_SERVER_HOST).save()`
- Add the `server` factory to each test
- Use the `faker` factory to generate emails, etc.
- Don't add obvious `assert` descriptions
- Do not use the `db_session` fixture here. Instead, use `with test_session():` if you need to setup complex database state
- if a UI timeout is occuring, it could be because it cannot find a element because the rendering has changed. Check the failure screenshot and see if you can correct the test assertion.
- The integration tests can take a very long time to run. Do not abort them if they are taking a long time.
- Use `expect(page.get_by_text("Screening is fully booked")).to_be_visible()` instead of `expect(page.get_by_role("heading")).to_contain_text("Screening is fully booked")`. It's less brittle.
- Do not use `client` fixtures in an integration test. Integration tests should only use the frontend of the website to interact with the application, not the API.
- Use `with page.expect_response("https://example.com/resource") as response_info:` to assert against network activity.
- Do not `next_button.evaluate("el => el.click()")` instead, just `locator.click()`. If this doesn't work, stop your work and let me know.
- Only use `wait_for_loading(page)` if a `LONG_INTEGRATION_TEST_TIMEOUT` on an expectation does not work: `expect(page.get_by_text("Your Matched Doctors")).to_be_visible(timeout=LONG_INTEGRATION_TEST_TIMEOUT)`
- Prefer fewer integration tests that cover more functionality. Unlike unit tests, where each test is designed to test a very particular piece of functionality, I want integration tests to cover entire workflows. It's preferred to add more steps to an integration test to test an entire workflow.
- Prefer simple locators. If a `filter`, `or_`, etc is required to capture a button in multiple states it indicates something is wrong in the code.
