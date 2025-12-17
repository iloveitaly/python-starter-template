---
applyTo: "**/*.py"
---

## Python App

- `app/lib/` is for code that is not specified to this application and with some effort could extracted into a external package.
- `app/helpers` is for larger reusable modules that if they weren't specific to this application, could be extracted into their own package.
- `app/utils` are small helper functions that are specific to a particular page or area of the application.
- `app/__init__.py` is the entrypoint for the application which is run when _anything_ is executed (fastapi, celery, etc).
  - It primarily runs `configure_*` commands for any `app.configuration.*` modules. These modules primary setup API clients, database connections, python language configuration, etc.
  - Also makes sure anything that mutates global state loads early.
- FastAPI server and routes are specified in `app/routes/`
- SQLModels are specified in `app/models/`
- Files within `app/commands/` should have:
  - Are not designed for CLI execution, but instead are interactor-style internal commands.
  - Should not be used on the queuing system
  - A `perform` function that is the main entry point for the command.
  - Look at existing commands for examples of how to structure the command.
  - Use `TypeIDType` for any parameters that are IDs of models.
- Files within `app/jobs/` should have:
  - Are designed for use on the queuing system.
  - A `perform` function that is the main entry point for the job.
  - Look at existing jobs for examples of how to structure the job.
  - Use `TypeIDType | str` for any parameters that are IDs of models.
- When referencing a command, use the full-qualified name, e.g. `app.commands.transcript_deletion.perform`.
- When queuing a job or `perform`ing it in a test, use the full-qualified name, e.g. `app.jobs.transcript_deletion.perform`.
- `app/cli/` is for scripts or CLI tools that are specific to the application.
