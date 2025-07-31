import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

// from: https://ui.shadcn.com/docs/installation/manual
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
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
