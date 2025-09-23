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
