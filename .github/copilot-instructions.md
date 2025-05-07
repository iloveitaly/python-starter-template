## All Languages

Instructions for all programming languages:

- If no language is specified, assume the latest version of python.
- If tokens or other secrets are needed, pull them from an environment variable
- Prefer early returns over nested if statements.
- Prefer `continue` within a loop vs nested if statements.
- Prefer smaller functions over larger functions. Break up logic into smaller chunks with well-named functions.
- Only add comments if the code is not self-explanatory. Do not add obvious code comments.
- When I ask you to write code, prioritize simplicity and legibility over covering all edge cases, handling all errors, etc.
- When a particular need can be met with a mature, reasonably adopted and maintained package, I would prefer to use that package rather than engineering my own solution.
- Never add error handling to recover gracefully from an error without being asked to do so. Fail hard and early with assertions and allowing exceptions to propagate whenever possible
- For any complex or critical task, ask any and all clarification questions needed before proceeding.

**DO NOT FORGET**: keep your responses short, dense, and without fluff. I am a senior, well-educated software engineer, and do not need long explanations.

## Python

When writing Python:

* Assume the latest python, version 3.13.
* Prefer Pathlib methods (including read and write methods, like `read_text`) over `os.path`, `open`, `write`, etc.
* Prefer modern typing: `list[str]` over `List[str]`, `dict[str, int]` over `Dict[str, int]`, etc.
* Use Pydantic models over dataclass or a typed dict.
* Use SQLAlchemy for generating any SQL queries.
* Use the `click` package for all command line argument parsing.
* Use `log.info("the message", the_variable=the_variable)` instead of `log.info("the message: %s", the_variable)` or `print` for logging
* Log messages should be lowercase with no leading or trailing whitespace.
* No variable interpolation in log messages.
* When a particular need can be met with a mature, reasonably adopted and maintained package, I would prefer to use that package rather than engineering my own solution.

## Shell Scripts

- Assume zsh for any shell scripts. The latest version of modern utilities like ripgrep (rg), fdfind (fd), bat, httpie (http), zq (zed), jq, procs, rsync are installed and you can request I install additional utilities.
