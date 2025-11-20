import { Role } from '../types'

interface JWTPayload {
  sub: string // username
  role: string
  user_id: number
  exp: number
}

export function decodeJWT(token: string): JWTPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      return null
    }

    const payload = parts[1]
    const decoded = JSON.parse(atob(payload))
    return decoded as JWTPayload
  } catch (error) {
    console.error('Failed to decode JWT:', error)
    return null
  }
}

export function getRoleFromToken(token: string): Role {
  const payload = decodeJWT(token)
  return payload?.role === Role.ADMIN ? Role.ADMIN : Role.CLIENT
}

export function getUsernameFromToken(token: string): string {
  const payload = decodeJWT(token)
  return payload?.sub || ''
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeJWT(token)
  if (!payload || !payload.exp) {
    return true
  }

  const now = Math.floor(Date.now() / 1000)
  return payload.exp < now
}
