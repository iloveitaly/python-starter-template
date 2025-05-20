---
applyTo: "web/app/routes/**/*.tsx"
---

- The primary export in a routes file should specify loaderData like `export default function PageName({ loaderData }: Route.ComponentProps)`
- When using an import from `~/configuration/client` (1) use `body:` for request params and (2) always `const { data, error } = await theCall()`

