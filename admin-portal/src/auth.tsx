import { jwtDecode } from "jwt-decode"
import { createContext, useCallback, useContext, useState, type ReactNode } from "react"
import { googleLogout } from "@react-oauth/google"

// Interface for decoded JWT token payload
interface DecodedUser {
    email: string
    name?: string
    picture?: string
    exp?: number // JWT expiration timestamp
    [key: string]: unknown
}

export interface AuthContext {
    isAuthenticated: boolean
    login: (token: string) => Promise<void>
    logout: () => void
    user: DecodedUser | null
}

const AuthContext = createContext<AuthContext | null>(null)

const key = 'auth.user'
function getStoredUser(): DecodedUser | null {
    const userString = localStorage.getItem(key)
    if (!userString) {
        return null
    }
    try {
        const user = JSON.parse(userString) as DecodedUser
        // Check if token has expired
        if (user?.exp) {
            const nowInSeconds = Math.floor(Date.now() / 1000)
            if (user.exp < nowInSeconds) {
                // Token expired, clear storage
                localStorage.removeItem(key)
                return null
            }
        }
        return user
    } catch {
        return null
    }
}

function setStoredUser(user: DecodedUser | null) {
    if (user) {
        localStorage.setItem(key, JSON.stringify(user))
    } else {
        localStorage.removeItem(key)
    }
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<DecodedUser | null>(getStoredUser())
    const isAuthenticated = !!user

    const logout = useCallback(async () => {
        googleLogout()
        setStoredUser(null)
        setUser(null)
    }, [])

    const login = useCallback(async (token: string): Promise<void> => {
        try {
            // Decode the JWT token and extract user profile info
            const user = jwtDecode<DecodedUser>(token)

            // Use environment variable for API URL, fallback to localhost
            const apiUrl = import.meta.env.VITE_API_URL
            const result = await fetch(`${apiUrl}/ghost/users/${user.email}`)

            if (!result.ok) {
                throw new Error(`Authorization failed: ${result.status} ${result.statusText}`)
            }

            setStoredUser(user)
            setUser(user)
        } catch (error) {
            console.error('Login error:', error)
            // Clear any stored user data on failure
            setStoredUser(null)
            setUser(null)
            throw new Error('Authentication failed. Please try again.')
        }
    }, [])

    return (
        <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}