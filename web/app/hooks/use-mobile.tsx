// https://github.com/shadcn-ui/ui/pull/10433#issuecomment-4274680596
import { useSyncExternalStore } from "react"

export function useIsMobile(mobileBreakpoint = 768) {
  return useSyncExternalStore(
    (callback) => {
      const mql = globalThis.matchMedia(
        `(max-width: ${(mobileBreakpoint - 1).toFixed(0)}px)`,
      )
      mql.addEventListener("change", callback)
      return () => {
        mql.removeEventListener("change", callback)
      }
    },
    () => window.innerWidth < mobileBreakpoint, // Client value
    () => false, // Server/Initial hydration value
  )
}
