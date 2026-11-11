import { useState } from "react"
import { href } from "react-router"

import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { getClient } from "~/configuration/clerk"
import {
  useLoginAsUserMutation,
  useUserListQuery,
} from "~/configuration/client"

import { invariant } from "@epic-web/invariant"

function AdminBar() {
  const { data, error } = useUserListQuery()
  const { mutateAsync: loginAsUser, isPending } = useLoginAsUserMutation()

  const [selectedUser, setSelectedUser] = useState("")

  const isSwitchUserDisabled = !selectedUser || isPending

  if (!data || error) {
    return
  }

  async function switchToSelectedUser() {
    if (!selectedUser) return

    await loginAsUser({ path: { user_id: selectedUser } })

    // redirect to the root, reloading the same page could 404 because of different object IDs
    window.location.replace(href("/"))
  }

  async function restoreSignedInUser() {
    const { user } = await getClient()
    invariant(user, "user should exist since getClient requires a login")

    await loginAsUser({ path: { user_id: user.id } })

    window.location.replace(href("/"))
  }

  return (
    <div className="fixed top-0 left-0 z-50 flex w-full items-center space-x-2 bg-white p-1 text-xs shadow">
      {data.current_user && (
        <div className="whitespace-nowrap">
          Clerk: {data.current_user.clerk_id} ID: {data.current_user.id} Email:{" "}
          {data.current_user.email}
        </div>
      )}
      <Select value={selectedUser} onValueChange={setSelectedUser}>
        <SelectTrigger className="ml-3 h-2 w-40 text-sm">
          <SelectValue placeholder="Select user" />
        </SelectTrigger>
        <SelectContent>
          {data.users.map((user) => (
            <SelectItem key={user.clerk_id} value={user.clerk_id}>
              {user.email} {user.clerk_id}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        onClick={switchToSelectedUser}
        disabled={isSwitchUserDisabled}
        size="sm"
        variant="link"
        className="ml-2 h-2"
      >
        Switch User
      </Button>
      {data.current_user && (
        <Button
          onClick={restoreSignedInUser}
          disabled={isPending}
          size="sm"
          variant="link"
          className="ml-2 h-2"
        >
          Logout
        </Button>
      )}
    </div>
  )
}

export default AdminBar
