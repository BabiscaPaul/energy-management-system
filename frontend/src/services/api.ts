import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  UserProfile,
  UserUpdateRequest,
  Device,
  DeviceCreateRequest,
  DeviceUpdateRequest,
  ApiError,
} from '../types'

const API_BASE = ''

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`
    try {
      const data = (await res.json()) as ApiError | unknown
      if (typeof data === 'object' && data && 'detail' in data) {
        message = (data as ApiError).detail ?? message
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(message)
  }

  if (res.status === 204 || res.status === 200) {
    const text = await res.text()
    if (!text) {
      return undefined as T
    }
    return JSON.parse(text) as T
  }

  return (await res.json()) as T
}

// Auth API
export const authAPI = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    return apiRequest<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    return apiRequest<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}

// Users API
export const usersAPI = {
  getAll: async (token: string): Promise<UserProfile[]> => {
    return apiRequest<UserProfile[]>('/api/users', {}, token)
  },

  getById: async (userId: number, token: string): Promise<UserProfile> => {
    return apiRequest<UserProfile>(`/api/users/${userId}`, {}, token)
  },

  update: async (
    userId: number,
    data: UserUpdateRequest,
    token: string,
  ): Promise<UserProfile> => {
    return apiRequest<UserProfile>(`/api/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, token)
  },

  delete: async (userId: number, token: string): Promise<{ message: string; id: number }> => {
    return apiRequest<{ message: string; id: number }>(`/api/users/${userId}`, {
      method: 'DELETE',
    }, token)
  },
}

// Devices API
export const devicesAPI = {
  getAll: async (token: string): Promise<Device[]> => {
    return apiRequest<Device[]>('/api/devices', {}, token)
  },

  getById: async (deviceId: number, token: string): Promise<Device> => {
    return apiRequest<Device>(`/api/devices/${deviceId}`, {}, token)
  },

  getByUserId: async (userId: number, token: string): Promise<Device[]> => {
    return apiRequest<Device[]>(`/api/devices/user/${userId}`, {}, token)
  },

  create: async (data: DeviceCreateRequest, token: string): Promise<Device> => {
    return apiRequest<Device>('/api/devices', {
      method: 'POST',
      body: JSON.stringify(data),
    }, token)
  },

  update: async (
    deviceId: number,
    data: DeviceUpdateRequest,
    token: string,
  ): Promise<Device> => {
    return apiRequest<Device>(`/api/devices/${deviceId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, token)
  },

  delete: async (deviceId: number, token: string): Promise<{ message: string; id: number }> => {
    return apiRequest<{ message: string; id: number }>(`/api/devices/${deviceId}`, {
      method: 'DELETE',
    }, token)
  },
}
