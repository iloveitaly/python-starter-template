from environs import Env
from marshmallow import ValidationError, missing

class StrictEnv(Env):
    """Environs that automatically enforces stripped + non-empty strings by default."""

    def str(self, name: str, default=missing, **kwargs):
        # By default, we want strict validation (non-empty, stripped)
        # If the user explicitly passes validate=None, we should disable strictness?
        # The prompt said: `config('OPTIONAL', default='') env.str('OPTIONAL', default='', validate=None) validate=None bypasses strict rule`

        # Current logic:
        # if kwargs.get("validate") is None: (True if missing OR explicit None)
        #   -> Adds strict validator.
        # This means validate=None ADDS validation instead of removing it.

        # Correct logic:
        # If "validate" is NOT in kwargs, add strict validation.
        # If "validate" IS in kwargs and is None, do NOTHING (allow empty).

        should_strip = False

        if "validate" not in kwargs:
            should_strip = True
            def _strict_validator(value):
                if not isinstance(value, str):
                    value = str(value)
                stripped = value.strip()
                if not stripped:
                    raise ValidationError(f"{name} must not be empty or whitespace-only")
            kwargs["validate"] = _strict_validator

        # If validate IS in kwargs (even if None), we respect it.
        # If validate=None passed, marshmallow does no validation.

        val = super().str(name, default=default, **kwargs)

        if should_strip and isinstance(val, str):
            return val.strip()

        return val


env = StrictEnv()
