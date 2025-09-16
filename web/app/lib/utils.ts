import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

// from: https://ui.shadcn.com/docs/installation/manual
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function isElementInViewport(el: Element | null): boolean {
  if (!el) return false

  const rect = el.getBoundingClientRect()

  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
      (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  )
}

// for query string usage in clientLoaders
export function getQueryParam(request: Request, key: string): string | null {
  const url = new URL(request.url)
  return url.searchParams.get(key)
}

export function getQueryParams(request: Request): Record<string, string> {
  const url = new URL(request.url)
  const params: Record<string, string> = {}

  for (const [key, value] of url.searchParams) {
    params[key] = value
  }

  return params
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function debounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number,
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}
