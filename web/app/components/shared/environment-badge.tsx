/**
 * only imported behind the `import.meta.env.VITE_ENVIRONMENT_BADGE` guard in root.tsx, so the component never ships to production
 *
 * tailwind scans all source files, so badge-only utilities can remain in production CSS even when the component is excluded
 */
export default function EnvironmentBadge() {
  return (
    <div className="pointer-events-none fixed bottom-2 left-2 z-[9999] rounded-[4px] bg-[#f59e0b] px-2 py-1 font-mono text-xs/normal font-semibold text-black">
      {import.meta.env.VITE_ENVIRONMENT_BADGE?.trim()}
    </div>
  )
}
