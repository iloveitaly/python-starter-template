import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { getClient } from "~/configuration/clerk"
import { loginAsUser } from "~/configuration/client"

import { useQuery } from "@tanstack/react-query"
import { userListOptions } from "client/@tanstack/react-query.gen"

function AdminBar() {
  const [selectedUser, setSelectedUser] = useState("")
  const { data, error } = useQuery({ ...userListOptions() })

  if (!data || error) {
    return
  }

  const handleLoginAs = async () => {
    if (!selectedUser) return

    await loginAsUser({ path: { user_id: selectedUser } })

    window.location.reload()
  }

  const handleLogout = async () => {
    await loginAsUser({ path: { user_id: (await getClient()).user.id } })

    window.location.reload()
  }

  return (
    <div className="fixed top-0 left-0 z-50 flex w-full items-center space-x-2 bg-white p-1 text-xs shadow">
      {data.current_user && (
        <div className="whitespace-nowrap">
          {data.current_user.clerk_id} {data.current_user.email}
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
        onClick={handleLoginAs}
        disabled={!selectedUser}
        size="sm"
        variant="link"
        className="ml-2 h-2"
      >
        Switch User
      </Button>
      {data.current_user && (
        <Button
          onClick={handleLogout}
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
