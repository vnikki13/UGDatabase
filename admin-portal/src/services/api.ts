// API service for backend calls
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export interface User {
  email: string
  name?: string
  picture?: string
}

export interface AuthorizationResponse {
  authorized: boolean
  user?: User
  message?: string
}

/**
 * Check if a user is authorized by their email
 * @param email - User's email from Google OAuth
 * @returns Promise with authorization result
 */
export async function checkUserAuthorization(email: string): Promise<AuthorizationResponse> {
  try {
    const response = await fetch(`${API_URL}/ghost/users/${email}`)
    
    if (response.ok) {
      const data = await response.json()
      return {
        authorized: true,
        user: data,
      }
    } else if (response.status === 401) {
      const error = await response.json()
      return {
        authorized: false,
        message: error.detail || 'User not authorized',
      }
    } else {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
  } catch (error) {
    console.error('Authorization check failed:', error)
    return {
      authorized: false,
      message: 'Failed to verify authorization. Please try again.',
    }
  }
}
