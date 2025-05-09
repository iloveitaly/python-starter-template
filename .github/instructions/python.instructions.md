
---
applyTo: "**/*.py"
---

When writing Python:

* Assume the latest python, version 3.13.
* Prefer Pathlib methods (including read and write methods, like `read_text`) over `os.path`, `open`, `write`, etc.
* Prefer modern typing: `list[str]` over `List[str]`, `dict[str, int]` over `Dict[str, int]`, etc.
* Use Pydantic models over dataclass or a typed dict.
* Use SQLAlchemy for generating any SQL queries.
* Use the `click` package for all command line argument parsing.
* Use `log.info("the message", the_variable=the_variable)` instead of `log.info("the message: %s", the_variable)` or `print` for logging. This object can be found at `from app import log`.
* Log messages should be lowercase with no leading or trailing whitespace.
* No variable interpolation in log messages.
* When a particular need can be met with a mature, reasonably adopted and maintained package, I would prefer to use that package rather than engineering my own solution.

### SQLModel & SQLAlchemy

When writing database models:

* Don't use `Field(...)` unless required. For instance, use `= None` instead of `= Field(default=None)`.
* Add enum classes close to where they are used, unless they are used across multiple classes (then put them at the top of the file)
* Use single double-quote docstrings (a string below the field definition) instead of comments to describe a field's purpose.
* Use `ModelName.foreign_key()` when generating a foreign key field

