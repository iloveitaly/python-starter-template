## Standalone Python Scripts

# Writing Standalone Python Scripts

Use this header:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
```

- Specify dependencies via the `dependencies` variable in the above comment
- Do not install packages with pip or any other package manager, assume packages will be installed when needed
- Use `click` for CLI interfaces
- Use `structlog_config` for logging. Read the usage guide: @https://github.com/iloveitaly/structlog-config/
