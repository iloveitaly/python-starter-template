---
applyTo: "**/*.py"
---
## Python


When writing Python:

* Assume the latest python, version 3.13.
* Prefer Pathlib methods (including read and write methods, like `read_text`) over `os.path`, `open`, `write`, etc.
* Use Pydantic models over dataclass or a typed dict.
* Use SQLAlchemy for generating any SQL queries.
* Use `click` for command line argument parsing.
* Use `log.info("the message", the_variable=the_variable)` instead of `log.info("The message: %s", the_variable)` or `print` for logging. This object can be found at `from app import log`.
  * Log messages should be lowercase with no leading or trailing whitespace.
  * No variable interpolation in log messages.
  * Do not coerce database IDs, dates, or Path objects to `str`
* Do not fix import ordering or other linting issues.
* Never edit or create any files in `migrations/versions/`
* Place all comments on dedicated lines immediately above the code statements they describe. Avoid inline comments appended to the end of code lines.
* Do not `try/catch` raw `Exceptions` unless explicitly told to. Prefer to let exceptions raise and cause an explicit error.

### Package Management

- Use `uv add` to add python packages. No need for `pip compile`, `pip install`, etc.

### Typing

* Assume the latest pyright version
* Prefer modern typing: `list[str]` over `List[str]`, `dict[str, int]` over `Dict[str, int]`, etc.
* Prefer to keep typing errors in place than eliminate type specificity:
  * Do not add ignore comments such as `# type: ignore`
  * Never add an `Any` type.
  * Do not `cast(object, ...)`

### Data Manipulation

* Prefer `funcy` utilities to complex list comprehensions or repetitive python statements.
* `import funcy as f` and `import funcy_pipe as fp`
* Some utilities to look at: `f.compact`

For example, instead of:

```python
params: dict[str, str] = {}
if city:
    params["city"] = city
if state_code:
    params["stateCode"] = state_code
```

Use:

```python
params = f.compact({"city": city, "stateCode": stateCode})
```

### Date & DateTime

* Use the `whenever` library for datetime + time instead of the stdlib date library. `Instant.now().format_iso()`
* DateTime mutation should explicitly opt in to a specific timezone `SystemDateTime.now().add(days=-7)`
