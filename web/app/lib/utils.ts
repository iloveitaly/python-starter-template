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
