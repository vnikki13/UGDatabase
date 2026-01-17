import { GoogleLogin, type CredentialResponse } from '@react-oauth/google'
import { useSessionToken } from '../hooks/useSessionToken'


export const LoginButton = () => {
    const { saveToken, getUserFromToken, logout } = useSessionToken()

    const handleSuccess = (response: CredentialResponse) => {
        const token = response?.credential
        if (!token) return
        saveToken(token)
        const user = getUserFromToken()
        console.log('User:', user)
    }

    const handleError = () => {
        console.error('Login failed')
    }

    return (
        <>
            <GoogleLogin onSuccess={handleSuccess} onError={handleError} />
            <button onClick={logout}>Logout</button>
        </>
    )
}

export default LoginButton

