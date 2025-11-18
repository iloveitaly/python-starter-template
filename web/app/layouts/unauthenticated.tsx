/**
 * Unauthenticated layout
 */
import { Outlet } from "react-router"

export default function UnauthenticatedLayout() {
  return (
    <div className="flex min-h-screen w-full flex-col">
      {/* flex-1 to allow the main content to grow and fill the available space, pushing the footer to the bottom */}
      <main className="mt-10 flex-1">
        <Outlet />
      </main>
    </div>
  )
}
