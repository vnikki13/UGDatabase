import { useEffect } from 'react'
import Alert from '@mui/material/Alert'
import Snackbar from '@mui/material/Snackbar'

const SUCCESS_DURATION = 4000
const ERROR_DURATION = 7000

interface FormStatusAlertsProps {
    errorMessage?: string | null
    successMessage?: string | null
    onCloseError?: () => void
    onCloseSuccess?: () => void
}

export function FormStatusAlerts({
    errorMessage,
    successMessage,
    onCloseError,
    onCloseSuccess,
}: FormStatusAlertsProps) {
    useEffect(() => {
        if (!successMessage) return
        const timer = setTimeout(() => onCloseSuccess?.(), SUCCESS_DURATION)
        return () => clearTimeout(timer)
    }, [successMessage, onCloseSuccess])

    useEffect(() => {
        if (!errorMessage) return
        const timer = setTimeout(() => onCloseError?.(), ERROR_DURATION)
        return () => clearTimeout(timer)
    }, [errorMessage, onCloseError])

    const snackbarSx = {
        position: 'fixed',
        bottom: { xs: 16, sm: 24 },
        left: { xs: '50%', sm: 'auto' },
        right: { xs: 'auto', sm: 24 },
        transform: { xs: 'translateX(-50%)', sm: 'none' },
        width: { xs: 'calc(100vw - 32px)', sm: 360 },
        maxWidth: '100%',
        zIndex: 1400,
    }

    return (
        <>
            <Snackbar
                open={!!successMessage}
                onClose={onCloseSuccess}
                sx={snackbarSx}
            >
                <Alert
                    severity="success"
                    onClose={onCloseSuccess}
                    variant="filled"
                    sx={{ width: '100%' }}
                >
                    {successMessage}
                </Alert>
            </Snackbar>
            <Snackbar
                open={!!errorMessage}
                onClose={onCloseError}
                sx={{ ...snackbarSx, bottom: { xs: successMessage ? 88 : 16, sm: successMessage ? 96 : 24 } }}
            >
                <Alert
                    severity="error"
                    onClose={onCloseError}
                    variant="filled"
                    sx={{ width: '100%' }}
                >
                    {errorMessage}
                </Alert>
            </Snackbar>
        </>
    )
}
