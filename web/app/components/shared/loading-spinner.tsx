import { Loader2 } from "lucide-react"

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-8">
      <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
      <span className="text-muted-foreground pl-3">Loading...</span>
    </div>
  )
}
