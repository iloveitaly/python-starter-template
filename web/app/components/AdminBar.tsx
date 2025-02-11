import React, { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const AdminBar: React.FC = () => {
  // Dummy constant for admin check
  const isAdmin = true // change for real auth check

  // Dummy current user information
  const currentUser = { id: "admin123", email: "admin@example.com" }

  // Dummy dropdown user options
  const userOptions = [
    { clerk_id: "user1", email: "user1@example.com" },
    { clerk_id: "user2", email: "user2@example.com" },
    { clerk_id: "user3", email: "user3@example.com" },
  ]

  const [selectedUser, setSelectedUser] = useState("")

  if (!isAdmin) return null

  const handleLoginAs = async () => {
    if (!selectedUser) return
    try {
      // await axios.post(`/admin/login_as/${selectedUser}`)
      window.location.reload()
    } catch (error) {
      console.error("login_as failed", error)
    }
  }

  const handleLogout = () => {
    // Add logout logic here; for now we simply reload the page.
    window.location.reload()
  }

  return (
    <div className="fixed top-0 left-0 z-50 flex w-full items-center space-x-2 bg-white p-1 text-xs shadow">
      <div className="whitespace-nowrap">
        {currentUser.id} ({currentUser.email})
      </div>
      <Select value={selectedUser} onValueChange={setSelectedUser}>
        <SelectTrigger className="ml-3 h-2 w-40 text-sm">
          <SelectValue placeholder="Select user" />
        </SelectTrigger>
        <SelectContent>
          {userOptions.map((user) => (
            <SelectItem key={user.clerk_id} value={user.clerk_id}>
              {user.email}
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
        login_as
      </Button>
      {currentUser && (
        <Button
          onClick={handleLogout}
          size="sm"
          variant="link"
          className="ml-2 h-2"
        >
          logout
        </Button>
      )}
    </div>
  )
}

export default AdminBar
