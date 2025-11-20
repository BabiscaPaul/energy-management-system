import { useState, useEffect } from 'react'
import type { UserProfile, AuthState, UserUpdateRequest } from '../types'
import { usersAPI } from '../services/api'
import { ProfileEditForm } from './ProfileEditForm'

interface UserManagementProps {
  auth: AuthState
}

export function UserManagement({ auth }: UserManagementProps) {
  const [users, setUsers] = useState<UserProfile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingUser, setEditingUser] = useState<UserProfile | null>(null)

  useEffect(() => {
    loadUsers()
  }, [])

  async function loadUsers() {
    setLoading(true)
    setError(null)
    try {
      const data = await usersAPI.getAll(auth.token)
      setUsers(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpdateUser(data: UserUpdateRequest) {
    if (!editingUser) return

    await usersAPI.update(editingUser.id, data, auth.token)
    setEditingUser(null)
    await loadUsers()
  }

  async function handleDeleteUser(userId: number) {
    if (!confirm('Are you sure you want to delete this user? This will also delete all their devices.')) {
      return
    }

    try {
      await usersAPI.delete(userId, auth.token)
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user')
    }
  }

  if (loading && users.length === 0) {
    return <div className="card"><p>Loading users...</p></div>
  }

  if (editingUser) {
    return (
      <div className="card">
        <ProfileEditForm
          profile={editingUser}
          onSave={handleUpdateUser}
          onCancel={() => setEditingUser(null)}
        />
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>User Management</h3>
        <button onClick={loadUsers} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      {users.length === 0 ? (
        <p>No users found.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Address</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.full_name}</td>
                <td>{user.email}</td>
                <td>{user.phone_number || '-'}</td>
                <td>{user.address || '-'}</td>
                <td className="actions">
                  <button onClick={() => setEditingUser(user)} className="btn-small">
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteUser(user.id)}
                    className="btn-small btn-danger"
                    disabled={user.id === auth.userId}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
