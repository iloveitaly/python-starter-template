import * as React from "react"

export function useIsMobile(mobileBreakpoint = 768) {
  // Subscribe to media query changes
  const subscribe = React.useCallback(
    (callback: () => void) => {
      const mql = window.matchMedia(`(max-width: ${mobileBreakpoint - 1}px)`)
      mql.addEventListener("change", callback)
      return () => mql.removeEventListener("change", callback)
    },
    [mobileBreakpoint],
  )

  // Get the current value from the window
  const getSnapshot = () => window.innerWidth < mobileBreakpoint

  // Provide a fallback value for Server-Side Rendering (Next.js, Remix, etc.)
  const getServerSnapshot = () => false

  return React.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
