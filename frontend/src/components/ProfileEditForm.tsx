import { useState, type FormEvent } from 'react'
import type { UserProfile, UserUpdateRequest } from '../types'

interface ProfileEditFormProps {
  profile: UserProfile
  onSave: (data: UserUpdateRequest) => Promise<void>
  onCancel: () => void
}

export function ProfileEditForm({ profile, onSave, onCancel }: ProfileEditFormProps) {
  const [fullName, setFullName] = useState(profile.full_name)
  const [email, setEmail] = useState(profile.email)
  const [phone, setPhone] = useState(profile.phone_number || '')
  const [address, setAddress] = useState(profile.address || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      await onSave({
        full_name: fullName,
        email,
        phone_number: phone || undefined,
        address: address || undefined,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="edit-form" onSubmit={handleSubmit}>
      <h3>Edit Profile</h3>
      {error && <div className="error-box">{error}</div>}
      
      <label>
        Full name
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />
      </label>

      <label>
        Email
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>

      <label>
        Phone number
        <input
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="Optional"
        />
      </label>

      <label>
        Address
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Optional"
        />
      </label>

      <div className="form-actions">
        <button type="button" onClick={onCancel} disabled={loading}>
          Cancel
        </button>
        <button type="submit" disabled={loading} className="primary">
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  )
}
