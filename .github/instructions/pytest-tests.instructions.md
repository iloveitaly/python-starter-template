---
applyTo: "tests/**/*.py"
---
## Pytest Tests

- Look to tests/factories.py to generate any required database state
  - Here's an example of how to create + persist a factory `DistributionFactory.save()`
- Use the `faker` factory to generate emails, etc.
- Do not mock or patch unless I instruct you to. Test as much of the application stack as possible in each test.
- If you get lazy attribute errors, use the `db_session` fixture
- If we are testing Stripe interactions, assume we want to hit the live sandbox API. Don't mock out Stripe interactions unless I explicitly instruct you to.
