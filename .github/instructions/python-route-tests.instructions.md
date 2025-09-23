---
applyTo: "tests/routes/**/*.py"
---
## Python Route Tests

- Polyfactory is the [factory](tests/factories.py) library in use. `ModelNameFactory.build()` is how you generate factories.
- Use `assert_status(response)` to check the response of a client
