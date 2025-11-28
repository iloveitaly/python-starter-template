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
  * Do not coerce database IDs or dates to `str`
* Do not fix import ordering or other linting issues.
* Never edit or create any files in `migrations/versions/`

### Typing

* Assume the latest pyright version
* Prefer modern typing: `list[str]` over `List[str]`, `dict[str, int]` over `Dict[str, int]`, etc.
* Prefer to keep typing errors in place than eliminate type specificity:
  * Do not add ignore comments such as `# type: ignore`
  * Never add an `Any` type.
  * Do not `cast(object, ...)`

### Date & DateTime

* Use the `whenever` library for datetime + time instead of the stdlib date library. `Instant.now().format_common_iso()`

### Database & ORM

When accessing database records:

* SQLModel (wrapping SQLAlchemy) is used
* `Model.one(primary_key)` or `Model.get(primary_key)` should be used to retrieve a single record
* Do not manage database sessions, these are managed by a custom tool
  * Use `TheModel(...).save()` to persist a record
  * Use `TheModel.where(...).order_by(...)` to query records. `.where()` returns a SQLAlchemy select object that you can further customize the query.

When writing database models:

* Don't use `Field(...)` unless required (i.e. when specifying a JSON type for a `dict` or pydantic model using `Field(sa_type=JSONB)`). For instance, use `= None` instead of `= Field(default=None)`.
* Add enum classes close to where they are used, unless they are used across multiple classes (then put them at the top of the file)
* Use `ModelName.foreign_key()` when generating a foreign key field
* Store currency as an integer, e.g. $1 = 100.

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

## Python App

* Files within `app/commands/` should have:
  * Are not designed for CLI execution, but instead are interactor-style internal commands.
  * Should not be used on the queuing system
  * A `perform` function that is the main entry point for the command.
  * Look at existing commands for examples of how to structure the command.
  * Use `TypeIDType` for any parameters that are IDs of models.
* Files within `app/jobs/` should have:
  * Are designed for use on the queuing system.
  * A `perform` function that is the main entry point for the job.
  * Look at existing jobs for examples of how to structure the job.
  * Use `TypeIDType | str` for any parameters that are IDs of models.
* When referencing a command, use the full-qualified name, e.g. `app.commands.transcript_deletion.perform`.
* When queuing a job or `perform`ing it in a test, use the full-qualified name, e.g. `app.jobs.transcript_deletion.perform`.

## Pytest Integration Tests

- Look to tests/factories.py to generate any required database state
  - Here's an example of how to create + persist a factory `DistributionFactory.build(domain=PYTHON_TEST_SERVER_HOST).save()`
- Add the `server` factory to each test
- Use the `faker` factory to generate emails, etc.
- Don't add obvious `assert` descriptions
- Do not use the `db_session` fixture here. Instead, use `with test_session():` if you need to setup complex database state

## Pytest Tests

- Look to tests/factories.py to generate any required database state
  - Here's an example of how to create + persist a factory `DistributionFactory.save()`
- Use the `faker` factory to generate emails, etc.
- Do not mock or patch unless I instruct you to. Test as much of the application stack as possible in each test.
- If you get lazy attribute errors, use the `db_session` fixture
- If we are testing Stripe interactions, assume we want to hit the live sandbox API. Don't mock out Stripe interactions unless I explicitly instruct you to.

## Python Route Tests

- Polyfactory is the [factory](tests/factories.py) library in use. `ModelNameFactory.build()` is how you generate factories.
- Use `assert_status(response)` to check the response of a client

## Alembic Migrations

### Data Migrations

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

## FastAPI

- When throwing a `HTTPException`, do not add a `detail=` and use a named status code (`status.HTTP_400_BAD_REQUEST`)
- Do not return a `dict`, instead create a `class RouteNameResponse`
  - Locate these classes right above the `def route_name():` function which uses them.

## React

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

## React Router

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

## React Router Client Loader

Do this in a `clientLoader` and use `loaderData` to render the component. DO NOT create mock data, new interfaces, or mock data loader functions. Instead, assume `loaderData` has all of the data you need to render the component.

## Shell

- Assume zsh for any shell scripts. The latest version of modern utilities like ripgrep (rg), fdfind (fd), bat, httpie (http), zq (zed), jq, procs, rsync are installed and you can request I install additional utilities.

## TypeScript

- Use `pnpm`, not `npm`
- Node libraries are not available
- Use `lib/` for generic code, `utils/` for project utilities, `hooks/` for React hooks, and `helpers/` for page-specific helpers.
- Prefer `function theName() {` over `const theName = () =>`
- Use `import { invariant } from @epic-web/invariant` instead of another invariant library
- Use `requireEnv("VITE_THE_ENV_VAR")` instead of `process.env.THE_ENV_VAR`

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

## TypeScript DocString

Add a file-level docstring with a simple description of what this file does and where this is used.

## Secrets

Here's how environment variables are managed in this application:

- `.envrc` entry point to load the correct env stack. Should not contain secrets and should be simple some shell logic and direnv stdlib calls.
- `.env` common configuration for all systems. No secrets. No dotenv/custom scripts. Just `export`s to modify core configuration settings like `export TZ=UTC`.
- `.env.local` overrides across all environments (dev and test). Useful for things like 1Password service account token and database hosts which mutate the logic followed in `.env.shared`. Not committed to source control.
- `.env.shared` This contains the bulk of your system configuration. Shared across test, CI, dev, etc but not production.
- `.env.shared.local` Override `.env.shared` configuration locally. Not committed to source.
- `.env.dev.local` configuration overrides for non-test environments. `PYTHONBREAKPOINT`, `LOG_LEVEL`, etc. Most of your environment changes end up happening here.
- `.env.test` test-only environment variables (`PYTHON_ENV=test`). This file should generally be short.
- `.env.production.{backend,frontend}` for most medium-sized projects you'll have separate frontend and backend systems (even if your frontend is SPA, which I'm a fan of). These two files enable you to document the variables required to build (in the case of a SPA frontend) or run (in the case of a python backend) your system in production.
- `*.local` files have a `-example` variant which is committed to version control. These document helpful environment variables for local development.
- When writing TypeScript/JavaScript/React, use `requireEnv("THE_ENV_VAR_NAME")` to read an environment variable. `import {requireEnv} from '~/utils/environment'`

## Fix Tests

Focus on all unit + command tests. Make sure they pass and fix errors. If you run into anything very odd stop, and let me know. Mutate test code first and let me know if you think you should update application code.

Then, focus on integration tests in tests/integration. If an integration test fails, run it again just to be sure it wasn't a flakey test (integration tests are not deterministic). If it fails because of a visual error, check the 'tmp/test-results/playwright/' directory for a screenshot relating to the failing test that you can inspect.

## Implement Fastapi Routes

The file docstring contains a description of the FastAPI routes we need to implement. Implement these routes.

Avoid implementing any Stripe logic right now. I will do that later. Leave TODOs for this and other areas where you are very unsure of what to do.

## Plan Only

As this point, I only want to talk about the plan. How would you do this? What would you refactor to make this design clean? You are an expert software engineer and I want you to think hard about how to plan this project out.

Do not worry about writing database migrations. You make any changes directly to app/models/ files.

Let's separate this into key sections:

1. Refactor
2. Data model
3. Utilities/helpers/lib
4. Routes

## Python Command

- we don't have to put everything in a single perform. You can use helper functions. Can you modularize the code a bit and use helper functions so it's easier to read?

## Refactor On Instructions

Refactor this code following all the established coding rules. Carefully review each rule.

