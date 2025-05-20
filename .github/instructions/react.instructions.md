---
applyTo: "**/*.tsx"
---

- Do not write any backend code. Just frontend logic.
- For any backend requirements, create mock responses. Use a function to return mock data so I can easily swap it out later.
- When creating mock data, always specify it in a dedicated `mock.ts` file
- Load mock data using a react router `clientLoader`. Use the Skeleton component to present a loading state.
- If a complex skeleton is needed, create a component function `LoadingSkeleton` in the same file.
- Store components for each major page or workflow in `src/components/$WORKFLOW_OR_PAGE_NAME`.
- Use lowercase dash separated words for file names.
- Use React 19, TypeScript, Tailwind CSS, and ShadCN components.
- Prefer function components, hooks over classes.
- Break up large components into smaller components, but keep them in the same file unless they can be generalized.
- Put any "magic" strings like API keys, hosts, etc into a "constants.ts" file.
- Only use a separate interface for component props if there are more than 4 props.
- Internally, store all currency values as integers and convert them to floats when rendering visually
- Never edit the `components/ui/*.tsx` files
- When building forms use React Hook Form.
- Include a two line breaks between any `useHook()` calls and any `useState()` definitions for a component.

### React Hook Form

Follow this structure when generating a form.

```tsx
const formSchema = z.object({
  field_name: z.string(),
  // additional schema definition
})

const form = useForm<z.infer<typeof formSchema>>({
  resolver: zodResolver(formSchema),
})

async function onSubmit(values: z.infer<typeof formSchema>) {
  // ...
}

return (
  <Form {...form}>
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* form fields */}
    </form>
  </Form>
)
```

