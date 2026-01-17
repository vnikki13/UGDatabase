// hooks/useSessionToken.ts
import { useCallback } from 'react'
import { jwtDecode } from 'jwt-decode'
import { googleLogout } from '@react-oauth/google'

export type AuthToken = string

// Interface for decoded JWT token payload
interface DecodedUser {
  sub: string
  email: string
  name?: string
  picture?: string
  exp?: number // JWT expiration timestamp
  [key: string]: unknown
}

const SESSION_KEY = 'googleToken'

export const useSessionToken = () => {
  /**
   * Save a Google ID token to sessionStorage
   * @param token - JWT token returned from Google login
   */
  const saveToken = useCallback((token: AuthToken): void => {
    sessionStorage.setItem(SESSION_KEY, token)
  }, [])

  /**
   * Retrieve the stored token from sessionStorage
   * @returns JWT token or null if not present
   */
  const getToken = useCallback((): AuthToken | null => {
    return sessionStorage.getItem(SESSION_KEY)
  }, [])

  /**
   * Remove the token from sessionStorage
   */
  const removeToken = useCallback((): void => {
    sessionStorage.removeItem(SESSION_KEY)
  }, [])

  /**
   * Logout the user by calling googleLogout and clearing session token
   */
  const logout = useCallback(() => {
    googleLogout()
    removeToken()
  }, [removeToken])

  /**
   * Check if a given token is expired based on the exp field
   */
  const isTokenExpired = useCallback((token: AuthToken): boolean => {
    try {
      const decoded = jwtDecode<DecodedUser>(token)
      if (!decoded.exp) return true
      const nowInSeconds = Math.floor(Date.now() / 1000)
      return decoded.exp < nowInSeconds
    } catch {
      return true
    }
  }, [])

  /**
   * Decode the stored JWT token and extract user profile info
   * @returns DecodedUser object or null if token is missing/invalid
   */
  const getUserFromToken = useCallback((): DecodedUser | null => {
    const token = getToken()
    if (!token || isTokenExpired(token)) {
      removeToken() // auto-clean if expired
      return null
    }
    try {
      return jwtDecode<DecodedUser>(token)
    } catch {
      return null
    }
  }, [getToken, isTokenExpired, removeToken])

  return {
    saveToken,
    getToken,
    removeToken,
    getUserFromToken,
    logout,
    isTokenExpired,
  }
}
