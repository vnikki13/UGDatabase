import { GoogleLogin, type CredentialResponse } from '@react-oauth/google'
import { useSessionToken } from '../hooks/useSessionToken'
import Alert from '@mui/material/Alert'
import { useState } from 'react'


export const LoginButton = () => {
    const { saveToken, getUserFromToken, logout } = useSessionToken()
    const [showSuccess, setShowSuccess] = useState(false)
    const [showError, setShowError] = useState(false)

    const handleSuccess = async (response: CredentialResponse) => {
        const token = response?.credential
        if (!token) return
        saveToken(token)
        const user = getUserFromToken()

        if (!user?.email) {
            setShowError(true)
            return
        }

        console.log('User:', user)

        try {
            const apiResponse = await fetch(`http://localhost:8000/api/v1/ghost/users/${user.email}`)            
            if (apiResponse.ok) {
                setShowSuccess(true)
            } else {
                setShowError(true)
            }
        } catch (error) {
            console.error('Authorization check failed:', error)
            setShowError(true)
        }
    }

    const handleError = () => {
        console.error('Login failed')
    }

    return (
        <>
            <GoogleLogin onSuccess={handleSuccess} onError={handleError} />
            {showSuccess && (
                <Alert severity="success" onClose={() => setShowSuccess(false)}>
                    Here is a gentle confirmation that your action was successful.
                </Alert>
            )}
            {showError && (
                <Alert severity="error" onClose={() => setShowError(false)}>
                    You do not have the permission to login.
                </Alert>
            )}
            <div style={{ height: 20 }}></div>
            <button onClick={logout}>Logout</button>
        </>
    )
}

export default LoginButton

