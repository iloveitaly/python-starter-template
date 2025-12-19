import { Loader2 } from "lucide-react"

import { cn } from "~/lib/utils"

interface LoadingSpinnerProps {
  message?: string
  className?: string
  iconSize?: "sm" | "md" | "lg"
  showText?: boolean
}

export function LoadingSpinner({
  message = "Loading...",
  className,
  iconSize = "md",
  showText = true,
}: LoadingSpinnerProps) {
  const iconSizes = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  }

  return (
    <div className={cn("flex items-center justify-center py-8", className)}>
      <Loader2
        className={cn("animate-spin text-blue-600", iconSizes[iconSize])}
      />
      {showText && (
        <span className="text-muted-foreground pl-3 text-sm sm:text-base">
          {message}
        </span>
      )}
    </div>
  )
}
