/**
 * Displaying server-side error messages.
 *
 * Used throughout the application to show validation errors, API errors, and other server responses.
 * Pass over a `root.serverError` from a form to display the error. Accepts other error types as well.
 *
 * Automatically scrolls to the error when it appears to improve user experience.
 */
import { useEffect, useRef } from "react"

import { AlertCircleIcon } from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

interface ServerErrorAlertProps {
  error?: { message?: string }
  className?: string
}

export function ServerErrorAlert({
  error,
  className = "mb-4",
}: ServerErrorAlertProps) {
  // need ref to scroll to the error
  const errorRef = useRef<HTMLDivElement>(null)

  // scroll to the error if it exists
  useEffect(() => {
    if (error?.message && errorRef.current) {
      errorRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      })
    }
  }, [error?.message])

  if (!error) {
    return null
  }

  const errorMessage =
    error?.message ??
    "An unknown error occurred. Please try again, and come back later if the error persists"

  return (
    <Alert ref={errorRef} variant="destructive" className={className}>
      <AlertCircleIcon />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{errorMessage}</AlertDescription>
    </Alert>
  )
}
