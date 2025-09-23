
Coding instructions for all programming languages:

- If no language is specified, assume the latest version of python.
- If tokens or other secrets are needed, pull them from an environment variable
- Prefer early returns over nested if statements.
- Prefer `continue` within a loop vs nested if statements.
- Prefer smaller functions over larger functions. Break up logic into smaller chunks with well-named functions.
- Only add comments if the code is not self-explanatory. Do not add obvious code comments.
- Do not remove existing comments.
- When I ask you to write code, prioritize simplicity and legibility over covering all edge cases, handling all errors, etc.
- When a particular need can be met with a mature, reasonably adopted and maintained package, I would prefer to use that package rather than engineering my own solution.
- Never add error handling to recover gracefully from an error without being asked to do so. Fail hard and early with assertions and allowing exceptions to propagate whenever possible
- When naming variables or functions, use names that describe the effect. For example, instead of `function handleClaimFreeTicket` (a function which opens a dialog box) use `function openClaimFreeTicketDialog`.

Use line breaks to organize code into logical groups. Instead of:

```python
if not client_secret_id:
    raise HTTPException(status.HTTP_400_BAD_REQUEST)
session_id = client_secret_id.split("_secret")[0]
```

Prefer:

```python
if not client_secret_id:
    raise HTTPException(status.HTTP_400_BAD_REQUEST)

session_id = client_secret_id.split("_secret")[0]
```

**DO NOT FORGET**: keep your responses short, dense, and without fluff. I am a senior, well-educated software engineer, and do not need long explanations.

### Agent instructions

Page careful attention to these instructions when running tests, generating database migrations, or otherwise figuring out how to navigate project development scripts.

- Run python tests with `pytest` only. Do not `cat` the output and do not use `-q`. If tests fail because of a configuration or system error, do not attempt to fix and let me know. I will fix it.
  - Start with running non-integration tests with `pytest --ignore=tests/integration` then just run the integration tests `pytest tests/integration`
  - When debugging integration tests look at `$PLAYWRIGHT_RESULT_DIRECTORY`. There's a directory for each test failure. In that directory you fill find a `failure.html` containing the rendered DOM of the page on failure and a screenshot of the contents. Use these to debug why it failed.
- Do not attempt to create or run database migrations. Pause your work and let me know you need a migration run.
