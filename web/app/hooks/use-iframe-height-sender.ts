/**
 * @fileoverview React hook for sending iframe height updates to parent window.
 *
 * This hook automatically detects when the component is embedded in an iframe and
 * continuously sends height updates to the parent window via postMessage. It handles:
 * - Initial height calculation on mount
 * - Resize event listening for window size changes
 * - Dynamic content changes via ResizeObserver
 * - Debounced messaging to prevent excessive updates
 * - Fallback to wildcard origin if referrer cannot be determined
 */
import { useEffect } from "react"
import { ComponentType } from "react"

import { debounce } from "~/lib/utils"

// Debounce time for height updates in milliseconds
const HEIGHT_UPDATE_DEBOUNCE_MS = 200

function getParentOrigin() {
  try {
    const referrer = document.referrer
    if (referrer) {
      return new URL(referrer).origin
    }
    return "*" // Fallback to wildcard if referrer is unavailable
  } catch (e) {
    console.warn("Could not determine parent origin:", e)
    return "*" // Fallback to wildcard
  }
}

export const useIframeHeightSender = () => {
  useEffect(() => {
    // Only run if embedded in an iframe
    if (window.self === window.top) {
      return // Not embedded; exit early
    }

    // Function to calculate and send height
    const sendHeight = () => {
      const height = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight,
        document.body.offsetHeight,
        document.documentElement.offsetHeight,
        document.body.clientHeight,
        document.documentElement.clientHeight,
      )

      window.parent.postMessage(
        {
          type: "heightUpdate",
          payload: { height },
        },
        getParentOrigin(),
      )
    }

    // Debounced version
    const debouncedSendHeight = debounce(sendHeight, HEIGHT_UPDATE_DEBOUNCE_MS)

    // Initial send after component mount (simulates 'load')
    debouncedSendHeight()

    // Set up window resize listener
    window.addEventListener("resize", debouncedSendHeight)

    // Set up ResizeObserver for dynamic content changes
    let resizeObserver: ResizeObserver | null = null
    if ("ResizeObserver" in window) {
      resizeObserver = new ResizeObserver(debouncedSendHeight)
      resizeObserver.observe(document.body)
    } else {
      console.warn(
        "ResizeObserver not supported; relying on resize event only.",
      )
    }

    // Cleanup on unmount
    return () => {
      window.removeEventListener("resize", debouncedSendHeight)
      if (resizeObserver) {
        resizeObserver.disconnect()
      }
    }
  }, []) // Empty dependency array: Runs once on mount
}

/**
 * Higher-order component that wraps any component with iframe height sending functionality.
 *
 * This function takes a React component and returns a new component that automatically
 * sends height updates to the parent window when embedded in an iframe. The wrapped
 * component will have the same props interface as the original.
 *
 * @example
 * ```tsx
 * const MyComponentWithHeightSender = withIFrameHeightSender(MyComponent)
 * ```
 */
export function withIFrameHeightSender<P extends object>(
  WrappedComponent: ComponentType<P>
) {
  return function WithIFrameHeightSender(props: P) {
    useIframeHeightSender()

    return <WrappedComponent {...props} />
  }
}
