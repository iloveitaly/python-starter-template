# Changelog

## [Unreleased]

### Changed
- Migrated environment configuration from `python-decouple` to `environs` (v14.x) with a custom `StrictEnv` implementation.
- **Breaking Change:** Environment variables are now strictly validated by default. Empty or whitespace-only strings will raise a `ValidationError` unless `validate=None` is explicitly passed.
- **Migration Guide:**
  - Replace `from decouple import config` with `from app.env import env`.
  - Use `env.str("KEY")` instead of `config("KEY")`.
  - Use `env.bool("KEY", False)` instead of `config("KEY", default=False, cast=bool)`.
  - Use `env.int("KEY")` instead of `config("KEY", cast=int)`.
  - To allow empty strings: `env.str("KEY", validate=None)`.
