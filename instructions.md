Coding instructions for all programming languages:

- Never use emojis anywhere unless explicitly requested.
- If no language is specified, assume the latest version of python.
- If tokens or other secrets are needed, pull them from an environment variable
- Prefer early returns over nested if statements.
- Prefer `continue` within a loop vs nested if statements.
- Prefer smaller functions over larger functions. Break up logic into smaller chunks with well-named functions.
- Prefer constants with separators: `10_000` is preferred to `10000` (or `10_00` over `1000` in the case of a integer representing cents).
- Only add comments if the code is not self-explanatory. Do not add obvious code comments.
- Do not remove existing comments.
- When I ask you to write code, prioritize simplicity and legibility over covering all edge cases, handling all errors, etc.
- When a particular need can be met with a mature, reasonably adopted and maintained package, I would prefer to use that package rather than engineering my own solution.
- Never add error handling to catch an error without being asked to do so. Fail hard and early with assertions and allow exceptions to propagate.
- When naming variables or functions, use names that describe the effect. For example, instead of `function handleClaimFreeTicket` (a function which opens a dialog box) use `function openClaimFreeTicketDialog`.
- Do not install missing system packages! Instead, ask me to install them for you.
- If terminal commands are failing because of missing variables or commands which are unrelated to your current task, stop your work and let me know.
- Don't worry about fixing lint errors or running lint scripts unless I specifically ask you to.

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

**DO NOT FORGET**: keep your responses short, dense, and without fluff. I am a senior, well-educated software engineer, and hate long explanations.

### Import Developer Workflow Rules

Pay careful attention to these instructions when running tests, generating database migrations, or otherwise figuring out how to operate this project:

- Run `just --list` to see all available pre-written workflow development commands.
- Run python code with `uv run python`
- Run python tests with `pytest` only. If tests fail because of a configuration or system error, do not attempt to fix and let me know. I will fix it.
  - Initially run `pytest --ignore=tests/integration` then only run `pytest tests/integration`
  - When debugging integration tests look at `$PLAYWRIGHT_RESULT_DIRECTORY`. There's a directory for each test failure. In that directory you fill find a `failure.html` containing the rendered DOM of the page on failure and a screenshot of the contents. Use these to debug why it failed.
- Do not attempt to create or run database migrations. Pause your work and let me know you need a migration run.
  - If you receive errors about missing migrations, missing tables, database connectivity, etc, stop your work and let me know.

Look at @local.md

## Alembic Migrations

globs: migrations/versions/*.py

### Default Content for New Non-Nullable Columns

To add a non-nullable column and set a specific value for all existing rows without a persistent server default:

```python
# 1. Add the column as nullable (no default needed):
op.add_column('distribution', sa.Column('default_campaign_ending_date', sa.DateTime(timezone=True), nullable=True))
# 2. Update existing rows with your desired value (e.g., a specific datetime)
op.execute("UPDATE distribution SET default_campaign_ending_date = %s", [datetime.utcnow()])
# 3. Alter the column to non-nullable:
op.alter_column('distribution', 'default_campaign_ending_date', nullable=False)
```

### Record Backfill Operations

For migrations that include data mutation, and not only schema modifications, use this pattern to setup a session:

```python
from alembic import op
from sqlmodel import Session
from activemodel.session_manager import global_session
from app import log

def run_migration_helper():
  pass

def upgrade() -> None:
  session = Session(bind=op.get_bind())

  with global_session(session):
      run_migration_helper()
      flip_point_coordinates()
      backfill_screening_host_data()

  # flush before running any other operations, otherwise not all changes will persist to the transaction
  session.flush()
```

However, if you don't need the business logic attached to the models, you can execute a query using `op.execute`:

```python
op.execute(
  TheModel.__table__.update().values({"a_field": "a_value"}) # type: ignore
)
```

## Fastapi

globs: app/routes/**/*.py

- When throwing a `HTTPException`, do not add a `detail=` and use a named status code (`status.HTTP_400_BAD_REQUEST`)
- Do not return a `dict`, instead create a `class RouteNameResponse`
  - Locate these classes right above the `def route_name():` function which uses them.
- Use `Model.one` when a record must exist in order for the business logic to succeed.
- Do not try/except `Model.one` when using a parameter from the request to pull a record. Let this exception bubble up.
- Use `model_id: Annotated[TypeIDType, Path()]` to represent a model ID as a URL path parameter

## Pytest Integration Tests

globs: tests/integration/**/*.py

- Look to tests/factories.py to generate any required database state
  - Here's an example of how to create + persist a factory `DistributionFactory.build(domain=PYTHON_TEST_SERVER_HOST).save()`
- Add the `server` factory to each test
- Use the `faker` factory to generate emails, etc.
- Don't add obvious `assert` descriptions
- Do not use the `db_session` fixture here. Instead, use `with test_session():` if you need to setup complex database state
- if a UI timeout is occuring, it could be because it cannot find a element because the rendering has changed. Check the failure screenshot and see if you can correct the test assertion.
- The integration tests can take a very long time to run. Do not abort them if they are taking a long time.
- Use `expect(page.get_by_text("Screening is fully booked")).to_be_visible()` instead of `expect(page.get_by_role("heading")).to_contain_text("Screening is fully booked")`. It's less brittle.
- Do not use `client` fixtures in an integration test. Integration tests should only use the frontend of the website to interact with the application, not the API.
- Use `with page.expect_response("https://example.com/resource") as response_info:` to assert against network activity.
- Do not `next_button.evaluate("el => el.click()")` instead, just `locator.click()`. If this doesn't work, stop your work and let me know.
- Only use `wait_for_loading(page)` if a `LONG_INTEGRATION_TEST_TIMEOUT` on an expectation does not work: `expect(page.get_by_text("Your Matched Doctors")).to_be_visible(timeout=LONG_INTEGRATION_TEST_TIMEOUT)`
- Prefer fewer integration tests that cover more functionality. Unlike unit tests, where each test is designed to test a very particular piece of functionality, I want integration tests to cover entire workflows. It's preferred to add more steps to an integration test to test an entire workflow.
- Prefer simple locators. If a `filter`, `or_`, etc is required to capture a button in multiple states it indicates something is wrong in the code.

## Pytest Tests

globs: tests/**/*.py

- Look to @tests/factories.py to generate any required database state
  - For example, to create and persist a `Distribution` record `DistributionFactory.save()`
  - If a factory doesn't exist for the model you are working with, create one.
  - You can customize one or more params in a factory using `DistributionFactory.save(host="custom_host.com)`
- Use the `faker` factory to generate emails, etc.
- Do not mock or patch unless I instruct you to. Test as much of the application stack as possible in each test.
- If you get lazy attribute errors, or need a database session to share across logic, use the `db_session` fixture to fix the issue.
  - Note that when writing route tests a `db_session` is not needed for the logic inside of the route.
- When testing Stripe, use the sandbox API. Never mock out Stripe interactions unless explicitly told to.
- Omit obvious docstrings and comments.

## Python App

globs: **/*.py

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

### Database & ORM

When accessing database records:

* SQLModel (wrapping SQLAlchemy) is used
* `Model.one(primary_key)` or `Model.get(primary_key)` should be used to retrieve a single record
* Do not manage database sessions, these are managed by a custom tool
  * Use `TheModel(...).save()` to persist a record
  * Use `TheModel.where(...).order_by(...)` to query records. `.where()` returns a SQLAlchemy select object that you can further customize the query.
  * To iterate over the records, you'll need to end your query chain with `.all()` which returns an interator: `TheModel.where(...)...all()`
* Instead of repulling a record `order = HostScreeningOrder.one(order.id)` refresh it using `order.refresh()`

When writing database models:

* Don't use `Field(...)` unless required (i.e. when specifying a JSON type for a `dict` or pydantic model using `Field(sa_type=JSONB)`). For instance, use `= None` instead of `= Field(default=None)`.
* Add enum classes close to where they are used, unless they are used across multiple classes (then put them at the top of the file)
* Use `ModelName.foreign_key()` when generating a foreign key field
* Store currency as an integer, e.g. $1 = 100.
* `before_save`, `after_save(self):`, `after_updated(self):` are lifecycle methods (modelled after ActiveRecord) you can use.

Example:

```python
class Distribution(
    BaseModel, TimestampsMixin, SoftDeletionMixin, TypeIDMixin("dst"), table=True
):
    """Triple-quoted strings for multi-line class docstring"""

    date_field_with_comment: datetime | None = None
    "use a string under the field to add a comment about the field"

    # no need to add a comment about an obvious field; no need for line breaks if there are no field-level docstrings
    title: str = Field(unique=True)
    state: str

    optional_field: str | None = None

    # here's how relationships are constructed
    doctor_id: TypeIDType = Doctor.foreign_key()
    doctor: Doctor = Relationship()

    @computed_field
    @property
    def order_count(self) -> int:
        return self.where(Order.distribution_id == self.id).count()
```

## Python Route Tests

globs: tests/routes/**/*.py

- Polyfactory is the [factory](tests/factories.py) library in use. `ModelNameFactory.build()` is how you generate factories.
- Use `assert_status(response)` instead of `assert response.status_code == status.HTTP_200_OK`
- Do not reference routes by raw strings. Instead of `client.get("/the/route/path")` use `client.get(api_app.url_path_for("route_method_name"))`

## Python

globs: **/*.py

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

## React Router

globs: web/app/routes/**/*.tsx

- You are using the latest version of React Router (v7).
- Always include the suffix `Page` when naming the default export of a route.
- The primary export in a routes file should specify `loaderData` like `export default function RouteNamePage({ loaderData }: Route.ComponentProps)`. `loaderData` is the return value from `clientLoader`.
- Use `href("/products/:id", { id: "abc123" })` to generate a url path for a route managed by the application.
  - Look at [routes.ts](mdc:web/app/routes.ts) to determine what routes and path parameters exist.
- Use `export async function clientLoader(loaderArgs: Route.ClientLoaderArgs)` to define a `clientLoader` on a route.
- Do not define `Route.*` types, these are autogenerated and can be imported from `import type { Route } from "./+types/routeFileName"`
- If URL parameters or query string values need to be checked before rendering the page, do this in a `clientLoader` and not in a `useEffect`
- Never worry about generating types using `pnpm`
- Use [`<AllMeta />`](web/app/components/shared/AllMeta.tsx) instead of MetaFunction or individual `<meta />` tags
- Use the following pattern to reference query string values (i.e. `?theQueryStringParam=value`)

```typescript
const [searchParams, _setSearchParams] = useSearchParams()
// searchParams contains the value of all query string parameters
const queryStringValue = searchParams.get("theQueryStringParam")
```

### Loading Mock Data

Don't load mock data in the component function with `useEffect`. Instead, load data in a `clientLoader`:

```typescript
// in mock.ts
export async function getServerData(options: any) {
  // ...
}

// in web/app/routes/**/*.ts
export async function clientLoader(loaderArgs: Route.ClientLoaderArgs) {
  // no error reporting is needed, this will be handled by the `getServerData`
  // mock loading functions should return result in a `data` key
  const { data } = await getServerData({
    /* ... */
  });

  // the return result here is available in `loaderData`
  return data;
}
```

### How to Use `clientLoader`

- `export async function clientLoader(loaderArgs: Route.ClientLoaderArgs) {`
- Load any server data required for page load here, not in the component function.
- Use `return redirect(href("/the/url"))` to redirect users
- Use [getQueryParam](web/app/lib/utils.ts) to get query string variables
- `throw new Response` if you need to mimic a 400, 500, etc error
- `loaderArgs` and all sub-objects are all fully typed
- `loaderArgs.params.id` to get URL parameters

### Loading Backend Data

- `~/configuration/client` re-exports all types and functions from `client/*`. Import from `~/configuration/client` instead of anything you find in the `client/` folder/package.
- For each API endpoint, there's a fully typed async function that can be used to call it. Never attempt to call an API endpoint directly.
  - Do not generate types for API parameters or responses. Reference the autogenerated types that are re-exported in `~/configuration/client`
  - For instance, the `getSignedUrl` function in [web/client/sdk.gen.ts] has a `SignedUrlResponse` type in [web/client/types.gen.ts]
  - This same type is used in the function signature, i.e. `type SignedUrlResponse = Awaited<ReturnType<typeof getSignedUrl>>["data"]`

- When using an import from `~/configuration/client`:
  - use `body:` for request params
  - always `const { data, error } = await theCall()`

`clientLoader` can only be used on initial page load within a route. If you need to load additional server data on component mount:

```tsx
import { useQuery } from "@tanstack/react-query"
import {
  // these options correspond to the server route
  createCheckoutSessionOptions,
  publicClient,
} from "~/configuration/client"

function TheComponent() {
  const { data, error } = useQuery({
    enabled: open,
    ...createCheckoutSessionOptions({
      // or `client` if authenticated
      client: publicClient,
      body: { /* API parameters here */ },
    }),
  })

  // remember to display errors by checking `error`
}
```

## React

globs: **/*.tsx

- You are using the latest version of React (v19)
- Do not write any backend code. Just frontend logic.
- If a complex skeleton is needed, create a component function `LoadingSkeleton` in the same file.
- Store components for each major page or workflow in `app/components/$WORKFLOW/$COMPONENT.tsx`.
  - If a single page has more than two dedicated components, create a subfolder `app/components/$WORKFLOW/$PAGE/$COMPONENT.tsx`
- Use lowercase dash separated words for file names.
- Use React 19, TypeScript, Tailwind CSS, and ShadCN components.
- Prefer function components, hooks over classes.
- Use ShadCN components in `web/app/components/ui` as your component library. If you need new components, ask for them.
  - Never edit the `web/components/ui/*.tsx` files.
  - You can find a list of components here https://ui.shadcn.com/docs/components
- Break up large components into smaller components, but keep them in the same file unless they can be generalized.
- Put any "magic" strings like API keys, hosts, etc into a "constants.ts" file.
- For React functional components with three or fewer props, always inline the prop types as an object literal directly in the function signature after the destructured parameters (e.g., `function Component({ prop1, prop2 }: { prop1: string; prop2?: number }) { ... })`. Include default values in destructuring and mark optional props with ? in the type object. Do not use separate interfaces or type aliases; keep types inline. For complex types, add inline comments if needed.
- Put the interface definition right above the related function
- Internally, store all currency values as integers and convert them to floats when rendering visually
- When building forms use React Hook Form.
- Include a two line breaks between any `useHook()` calls and any `useState()` definitions for a component.
- When using a function prop inside a `useEffect`, please use a pattern that avoids including the function in the dependency array, like the `useRef` trick.
- When writing React components, always hoist complex conditional expressions into descriptively named constants at the top of the component function for better readability and maintainability.
- When managing API response data, store the entire response object (or relevant subset) in a single `useState` rather than creating separate state variables for each field. Derive individual values from the response object when passing to child components using optional chaining (e.g., response?.field || defaultValue).
- Refactor ternary to &&: `{condition ? <A/> : <B/>}` → `{condition && <A/>}{!condition && <B/>}`
- Use the following pattern to reference query string values (i.e. `?theQueryStringParam=value`):

```typescript
const [searchParams, _setSearchParams] = useSearchParams();
// searchParams contains the value of all query string parameters
const queryStringValue = searchParams.get("theQueryStringParam")
```

### Mock Data

- For any backend communication, create mock responses. Use a async function to return mock data that I will swap out later for a async call to an API.
- When creating mock data, always specify it in a dedicated `web/app/mock.ts` file
- Load mock data using a react router `clientLoader`. Use the Skeleton component to present a loading state.

### React Hook Form

Follow this structure when generating a form.

```tsx

// add a mock function simulating server communication
async function descriptiveServerSendFunction(values: any) {
  const mockData = getMockReturnData(/* ... */)
  return new Promise(resolve => setTimeout(() => resolve(mockData), 500));
}

const formSchema = z.object({
  field_name: z.string(),
  // additional schema definition
})

const form = useForm<z.infer<typeof formSchema>>({
  resolver: zodResolver(formSchema),
})

const {
  formState: { isSubmitting, errors },
  setError,
  clearErrors,
} = form


async function onSubmit(values: z.infer<typeof formSchema>) {
  clearErrors("root")

  // ...
  const { data, error } = await descriptiveSendFunction(values)

  if (error) {
    setError("root.serverError", { message: error.detail?.[0]?.msg })
    return
  }
  // ...
}

return (
  <Form {...form}>
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* form fields */}

      <ServerErrorAlert error={errors.root?.serverError} />

      <Button
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? "Submitting..." : "Submit"}
      </Button>
    </form>
  </Form>
)
```

### Styling

* Use `text-blue-link` for styling any simple `<a>` tags

## Shell

globs: **/*.sh

- Assume zsh for any shell scripts. The latest version of modern utilities like ripgrep (rg), fdfind (fd), bat, httpie (http), zq (zed), jq, procs, rsync are installed and you can request I install additional utilities.

## Typescript

globs: **/*.ts,**/*.tsx

- Use `pnpm` or `pnpx` and not `npm` or `npx`.
  - Use `just js_shadcn`, `just pnpm`, and `just js_lint` instead of executing these operations exactly. @just/javascript.just
- Node libraries are not available
- Use `lib/` for generic code, `utils/` for project utilities, `hooks/` for React hooks, and `helpers/` for page-specific helpers.
- Prefer `function theName() {` over `const theName = () =>`
- Use `import { invariant } from @epic-web/invariant` instead of another invariant library
- Use `requireEnv("VITE_THE_ENV_VAR")` instead of `process.env.THE_ENV_VAR`
- Don't use `console.{log,error}`. Use `from ~/configuration/logging import log` and `log.info("string", {structured: "log"})` instead.

Here's how frontend code is organized in `web/app/`:

- `lib/` not specific to the project. This code could be a separate package at some point.
- `utils/` project-specific code, but not specific to a particular page.
- `helpers/` page- or section-specific code that is not a component, hook, etc.
- `hooks/` react hooks.
- `configuration/` providers, library configuration, and other setup code.
- `components/` react components.
  - `ui/` reusable ShadCN UI components (buttons, forms, etc.).
  - `shared/` components shared across multiple pages.
  - create additional folders for route- or section-specific components.

