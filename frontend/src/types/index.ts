export const Role = {
  ADMIN: 'admin',
  CLIENT: 'client',
} as const

export type Role = typeof Role[keyof typeof Role]

export interface AuthState {
  token: string
  userId: number
  role: Role
  username: string
}

export interface UserProfile {
  id: number
  full_name: string
  email: string
  phone_number?: string | null
  address?: string | null
}

export interface Device {
  id: number
  name: string
  max_consumption_value: number
  user_id: number
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  full_name: string
  email: string
  role?: Role
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: number
}

export interface UserUpdateRequest {
  full_name?: string
  email?: string
  phone_number?: string
  address?: string
}

export interface DeviceCreateRequest {
  name: string
  max_consumption_value: number
  user_id: number
}

export interface DeviceUpdateRequest {
  name?: string
  max_consumption_value?: number
  user_id?: number
}

export interface ApiError {
  detail?: string
}
