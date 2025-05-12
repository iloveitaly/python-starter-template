---
applyTo: "**/*.tsx"
---

1. Do not write any backend code. Just frontend logic.
2. For any backend requirements, create mock responses. Use a function to return mock data so I can easily swap it out later.
3. When creating mock data, always specify it in a dedicated `mock.ts` file
4. Load mock data using a react router `clientLoader`. Use the Skeleton component to present a loading state.
5. Store components for each major page or workflow in `src/components/$WORKFLOW_OR_PAGE_NAME`.
6. Use lowercase dash separated words for file names.
8. Use React 19, TypeScript, Tailwind CSS, and ShadCN components.
9. Prefer functional components, hooks over classes.
10. Break up large components into smaller components, but keep them in the same file unless they can be generalized.
11. Put any "magic" strings like API keys, hosts, etc into a "constants.ts" file.
12. Only use a separate interface for component props if there are more than 4 props.
13. Internally, store all currency values as integers and convert them to floats when rendering visually
14. use `pnpm` not `npm`
15. Node libraries are not available
16. Never edit the `components/ui/*.tsx` files
