import React, { useState } from "react"

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

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        backgroundColor: "#f5f5f5",
        padding: "10px",
        boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
        zIndex: 9999,
      }}
    >
      <span>
        User ID: {currentUser.id} | Email: {currentUser.email}
      </span>
      <select
        value={selectedUser}
        onChange={(e) => setSelectedUser(e.target.value)}
        style={{ marginLeft: "20px" }}
      >
        <option value="">Select user</option>
        {userOptions.map((user) => (
          <option key={user.clerk_id} value={user.clerk_id}>
            {user.email}
          </option>
        ))}
      </select>
      <button
        onClick={handleLoginAs}
        disabled={!selectedUser}
        style={{ marginLeft: "10px" }}
      >
        login_as
      </button>
    </div>
  )
}

export default AdminBar
