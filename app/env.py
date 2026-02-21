"""
All environment variables should be pulled from this file.

- We want loud, obvious errors when a variable doesn't exist in production that should
- Vars should be typed as strictly as possible
- Vars should be sourced close to where they are used (this is why we aren't using pydantic-settings)

This is a separate, simple module, to avoid circular imports.
"""

from environs import Env
from marshmallow import ValidationError, missing


class StrictEnv(Env):
    """
    Environs that automatically enforces stripped + non-empty strings by default.
    """

    def str(self, name: str, default=missing, **kwargs):
        """
        Returns a string environment variable, enforcing strict validation unless 'validate' is explicitly provided.

        If 'validate' is not in kwargs, adds a validator requiring non-empty, stripped strings.
        If 'validate' is in kwargs (even None), disables strict validation.
        """
        should_strip = False

        if "validate" not in kwargs:
            should_strip = True

            def _strict_validator(value):
                if not isinstance(value, str):
                    value = str(value)
                stripped = value.strip()
                if not stripped:
                    raise ValidationError(
                        f"{name} must not be empty or whitespace-only"
                    )

            kwargs["validate"] = _strict_validator

        # If validate IS in kwargs (even if None), we respect it.
        # If validate=None passed, marshmallow does no validation.

        val = super().str(name, default=default, **kwargs)

        if should_strip and isinstance(val, str):
            return val.strip()

        return val


env = StrictEnv()
