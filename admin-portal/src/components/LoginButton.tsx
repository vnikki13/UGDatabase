import { GoogleLogin, type CredentialResponse } from '@react-oauth/google'
import Alert from '@mui/material/Alert'
import { useState } from 'react'
import { useNavigate, useRouter } from '@tanstack/react-router'
import { useAuth } from '../auth'

const dashboard = '/dashboard' as const

export const LoginButton = () => {
    const auth = useAuth()
    const router = useRouter()
    const navigate = useNavigate()
    const [showError, setShowError] = useState(false)

    const handleSuccess = async (response: CredentialResponse) => {
        const token = response?.credential
        if (!token) return
        auth.login(token)
            .then(async () => {
                await router.invalidate()
                await navigate({ to: dashboard })
            })
            .catch(() => {
                setShowError(true)
            })
    }

    const handleError = () => {
        console.error('Login failed')
    }

    return (
        <>
            <GoogleLogin
                onSuccess={handleSuccess}
                onError={handleError}
            />
            {showError && (
                <Alert sx={{ margin: 5 }} severity="error" onClose={() => setShowError(false)}>
                    You do not have permission to access this dashboard.
                </Alert>
            )}
        </>
    )
}

export default LoginButton

