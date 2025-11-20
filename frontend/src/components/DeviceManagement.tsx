import { useState, useEffect, type FormEvent } from 'react'
import type { Device, AuthState, DeviceCreateRequest, DeviceUpdateRequest, UserProfile } from '../types'
import { devicesAPI, usersAPI } from '../services/api'

interface DeviceManagementProps {
  auth: AuthState
}

export function DeviceManagement({ auth }: DeviceManagementProps) {
  const [devices, setDevices] = useState<Device[]>([])
  const [users, setUsers] = useState<UserProfile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingDevice, setEditingDevice] = useState<Device | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [devicesData, usersData] = await Promise.all([
        devicesAPI.getAll(auth.token),
        usersAPI.getAll(auth.token),
      ])
      setDevices(devicesData)
      setUsers(usersData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateDevice(data: DeviceCreateRequest) {
    await devicesAPI.create(data, auth.token)
    setShowCreateForm(false)
    await loadData()
  }

  async function handleUpdateDevice(deviceId: number, data: DeviceUpdateRequest) {
    await devicesAPI.update(deviceId, data, auth.token)
    setEditingDevice(null)
    await loadData()
  }

  async function handleDeleteDevice(deviceId: number) {
    if (!confirm('Are you sure you want to delete this device?')) {
      return
    }

    try {
      await devicesAPI.delete(deviceId, auth.token)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete device')
    }
  }

  function getUserName(userId: number): string {
    const user = users.find((u) => u.id === userId)
    return user?.full_name || `User ${userId}`
  }

  if (loading && devices.length === 0) {
    return <div className="card"><p>Loading devices...</p></div>
  }

  if (showCreateForm) {
    return (
      <div className="card">
        <DeviceForm
          users={users}
          onSubmit={(data) => handleCreateDevice(data as DeviceCreateRequest)}
          onCancel={() => setShowCreateForm(false)}
        />
      </div>
    )
  }

  if (editingDevice) {
    return (
      <div className="card">
        <DeviceForm
          device={editingDevice}
          users={users}
          onSubmit={(data) => handleUpdateDevice(editingDevice.id, data as DeviceUpdateRequest)}
          onCancel={() => setEditingDevice(null)}
        />
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>Device Management</h3>
        <div>
          <button onClick={() => setShowCreateForm(true)} className="primary">
            Create Device
          </button>
          <button onClick={loadData} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      {devices.length === 0 ? (
        <p>No devices found.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Max Consumption</th>
              <th>Assigned User</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((device) => (
              <tr key={device.id}>
                <td>{device.id}</td>
                <td>{device.name}</td>
                <td>{device.max_consumption_value}</td>
                <td>{getUserName(device.user_id)}</td>
                <td className="actions">
                  <button onClick={() => setEditingDevice(device)} className="btn-small">
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteDevice(device.id)}
                    className="btn-small btn-danger"
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

interface DeviceFormProps {
  device?: Device
  users: UserProfile[]
  onSubmit: (data: DeviceCreateRequest | DeviceUpdateRequest) => Promise<void>
  onCancel: () => void
}

function DeviceForm({ device, users, onSubmit, onCancel }: DeviceFormProps) {
  const [name, setName] = useState(device?.name || '')
  const [maxConsumption, setMaxConsumption] = useState(device?.max_consumption_value.toString() || '')
  const [userId, setUserId] = useState(device?.user_id.toString() || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      await onSubmit({
        name,
        max_consumption_value: parseInt(maxConsumption, 10),
        user_id: parseInt(userId, 10),
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Operation failed')
      setLoading(false)
    }
  }

  return (
    <form className="edit-form" onSubmit={handleSubmit}>
      <h3>{device ? 'Edit Device' : 'Create Device'}</h3>
      {error && <div className="error-box">{error}</div>}

      <label>
        Device Name
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </label>

      <label>
        Max Consumption (Watts)
        <input
          type="number"
          value={maxConsumption}
          onChange={(e) => setMaxConsumption(e.target.value)}
          required
          min="0"
        />
      </label>

      <label>
        Assign to User
        <select value={userId} onChange={(e) => setUserId(e.target.value)} required>
          <option value="">Select a user...</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.full_name} (ID: {user.id})
            </option>
          ))}
        </select>
      </label>

      <div className="form-actions">
        <button type="button" onClick={onCancel} disabled={loading}>
          Cancel
        </button>
        <button type="submit" disabled={loading} className="primary">
          {loading ? 'Saving...' : device ? 'Update Device' : 'Create Device'}
        </button>
      </div>
    </form>
  )
}
