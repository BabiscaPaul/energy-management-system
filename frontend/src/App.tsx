import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import type { AuthState, UserProfile, Device, UserUpdateRequest } from './types'
import { authAPI, usersAPI, devicesAPI } from './services/api'
import { getRoleFromToken, getUsernameFromToken } from './utils/jwt'
import { ProfileEditForm } from './components/ProfileEditForm'
import { UserManagement } from './components/UserManagement'
import { DeviceManagement } from './components/DeviceManagement'
import { Role } from './types'

type Tab = 'dashboard' | 'users' | 'devices'

function App() {
  const [auth, setAuth] = useState<AuthState | null>(null)
  const [isRegisterMode, setIsRegisterMode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')

  const [loginUsername, setLoginUsername] = useState('')
  const [loginPassword, setLoginPassword] = useState('')

  const [regFullName, setRegFullName] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regUsername, setRegUsername] = useState('')
  const [regPassword, setRegPassword] = useState('')

  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [devices, setDevices] = useState<Device[]>([])
  const [dataLoading, setDataLoading] = useState(false)
  const [isEditingProfile, setIsEditingProfile] = useState(false)

  useEffect(() => {
    if (!auth) {
      setProfile(null)
      setDevices([])
      return
    }

    const loadData = async () => {
      try {
        setDataLoading(true)
        setError(null)

        const [user, userDevices] = await Promise.all([
          usersAPI.getById(auth.userId, auth.token),
          devicesAPI.getByUserId(auth.userId, auth.token),
        ])

        setProfile(user)
        setDevices(userDevices)
      } catch (err) {
        console.error(err)
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setDataLoading(false)
      }
    }

    void loadData()
  }, [auth])

  async function handleLogin(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data = await authAPI.login({ username: loginUsername, password: loginPassword })
      const role = getRoleFromToken(data.access_token)
      const username = getUsernameFromToken(data.access_token)
      setAuth({ token: data.access_token, userId: data.user_id, role, username })
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data = await authAPI.register({
        username: regUsername,
        password: regPassword,
        full_name: regFullName,
        email: regEmail,
      })
      const role = getRoleFromToken(data.access_token)
      const username = getUsernameFromToken(data.access_token)
      setAuth({ token: data.access_token, userId: data.user_id, role, username })
      // Clear register form
      setRegFullName('')
      setRegEmail('')
      setRegUsername('')
      setRegPassword('')
      setIsRegisterMode(false)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpdateProfile(data: UserUpdateRequest) {
    if (!auth || !profile) return

    const updated = await usersAPI.update(auth.userId, data, auth.token)
    setProfile(updated)
    setIsEditingProfile(false)
  }

  async function handleDeleteAccount() {
    if (!auth) return

    if (!confirm('Are you sure you want to delete your account? This action cannot be undone and will delete all your devices.')) {
      return
    }

    try {
      await usersAPI.delete(auth.userId, auth.token)
      handleLogout()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete account')
    }
  }

  function handleLogout() {
    setAuth(null)
    setProfile(null)
    setDevices([])
    setError(null)
    setActiveTab('dashboard')
    setIsEditingProfile(false)
  }

  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Energy Management System</h1>
      </header>

      {!auth ? (
        <main className="auth-layout">
          <div className="auth-toggle">
            <button
              type="button"
              className={!isRegisterMode ? 'active' : ''}
              onClick={() => {
                setIsRegisterMode(false)
                setError(null)
              }}
            >
              Login
            </button>
            <button
              type="button"
              className={isRegisterMode ? 'active' : ''}
              onClick={() => {
                setIsRegisterMode(true)
                setError(null)
              }}
            >
              Register
            </button>
          </div>

          {error && <div className="error-box">{error}</div>}

          {isRegisterMode ? (
            <form className="card" onSubmit={handleRegister}>
              <h2>Create account</h2>
              <label>
                Full name
                <input
                  type="text"
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  required
                />
              </label>
              <label>
                Username
                <input
                  type="text"
                  value={regUsername}
                  onChange={(e) => setRegUsername(e.target.value)}
                  required
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  required
                />
              </label>
              <button type="submit" disabled={loading}>
                {loading ? 'Creating account…' : 'Register'}
              </button>
            </form>
          ) : (
            <form className="card" onSubmit={handleLogin}>
              <h2>Sign in</h2>
              <label>
                Username
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  required
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  required
                />
              </label>
              <button type="submit" disabled={loading}>
                {loading ? 'Signing in…' : 'Login'}
              </button>
            </form>
          )}
        </main>
      ) : (
        <main className="dashboard">
          <div className="dashboard-header">
            <div>
              <h2>Energy Management System</h2>
              <p className="dashboard-caption">
                Welcome, {auth.username} <span className="role-badge role-{auth.role}">{auth.role.toUpperCase()}</span>
              </p>
            </div>
            <button type="button" onClick={handleLogout}>
              Logout
            </button>
          </div>

          <nav className="tabs">
            <button
              className={activeTab === 'dashboard' ? 'active' : ''}
              onClick={() => setActiveTab('dashboard')}
            >
              Dashboard
            </button>
            {auth.role === Role.ADMIN && (
              <>
                <button
                  className={activeTab === 'users' ? 'active' : ''}
                  onClick={() => setActiveTab('users')}
                >
                  Users
                </button>
                <button
                  className={activeTab === 'devices' ? 'active' : ''}
                  onClick={() => setActiveTab('devices')}
                >
                  Devices
                </button>
              </>
            )}
          </nav>

          {error && <div className="error-box">{error}</div>}

          {activeTab === 'dashboard' && (
            <section className="grid">
              <div className="card">
                <div className="card-header">
                  <h3>Your profile</h3>
                  {!isEditingProfile && profile && (
                    <button onClick={() => setIsEditingProfile(true)} className="btn-small">
                      Edit Profile
                    </button>
                  )}
                </div>
                {dataLoading && !profile ? (
                  <p>Loading profile…</p>
                ) : isEditingProfile && profile ? (
                  <ProfileEditForm
                    profile={profile}
                    onSave={handleUpdateProfile}
                    onCancel={() => setIsEditingProfile(false)}
                  />
                ) : profile ? (
                  <>
                    <dl className="info-list">
                      <div>
                        <dt>User ID</dt>
                        <dd>{profile.id}</dd>
                      </div>
                      <div>
                        <dt>Full name</dt>
                        <dd>{profile.full_name}</dd>
                      </div>
                      <div>
                        <dt>Email</dt>
                        <dd>{profile.email}</dd>
                      </div>
                      {profile.phone_number && (
                        <div>
                          <dt>Phone</dt>
                          <dd>{profile.phone_number}</dd>
                        </div>
                      )}
                      {profile.address && (
                        <div>
                          <dt>Address</dt>
                          <dd>{profile.address}</dd>
                        </div>
                      )}
                    </dl>
                    <div className="danger-zone">
                      <button onClick={handleDeleteAccount} className="btn-danger">
                        Delete My Account
                      </button>
                    </div>
                  </>
                ) : (
                  <p>No profile information found.</p>
                )}
              </div>

              <div className="card">
                <h3>Your devices</h3>
                {dataLoading && !devices.length ? (
                  <p>Loading devices…</p>
                ) : devices.length === 0 ? (
                  <p>You have no devices assigned.</p>
                ) : (
                  <table className="device-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Max consumption</th>
                      </tr>
                    </thead>
                    <tbody>
                      {devices.map((d) => (
                        <tr key={d.id}>
                          <td>{d.id}</td>
                          <td>{d.name}</td>
                          <td>{d.max_consumption_value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
          )}

          {activeTab === 'users' && auth.role === Role.ADMIN && (
            <UserManagement auth={auth} />
          )}

          {activeTab === 'devices' && auth.role === Role.ADMIN && (
            <DeviceManagement auth={auth} />
          )}
        </main>
      )}
    </div>
  )
}

export default App