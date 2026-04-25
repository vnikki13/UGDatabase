import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import { FormStatusAlerts } from './FormStatusAlerts'

interface FormActionFooterProps {
    canSubmit: boolean
    submitLabel: string
    busyLabel?: string
    isSubmitting?: boolean
    isBusy?: boolean
    successMessage?: string | null
    errorMessage?: string | null
    onCloseSuccess?: () => void
    onCloseError?: () => void
    disableReset?: boolean
    disableSubmit?: boolean
}

export function FormActionFooter({
    canSubmit,
    submitLabel,
    busyLabel,
    isSubmitting = false,
    isBusy = false,
    successMessage,
    errorMessage,
    onCloseSuccess,
    onCloseError,
    disableReset = false,
    disableSubmit = false,
}: FormActionFooterProps) {
    const effectiveSubmitLabel = isBusy && busyLabel ? busyLabel : submitLabel

    return (
        <Box sx={{ width: '100%', mt: 3 }}>
            <FormStatusAlerts
                successMessage={successMessage}
                errorMessage={errorMessage}
                onCloseSuccess={onCloseSuccess}
                onCloseError={onCloseError}
            />
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column-reverse', sm: 'row' },
                    alignItems: { xs: 'stretch', sm: 'center' },
                    justifyContent: 'center',
                    gap: 1.5,
                    width: '100%',
                }}
            >
                <Button type="reset" variant="outlined" disabled={disableReset} fullWidth={false}>
                    Reset
                </Button>
                <Button
                    type="submit"
                    variant="contained"
                    disabled={!canSubmit || disableSubmit}
                    loading={isSubmitting}
                    fullWidth={false}
                >
                    {effectiveSubmitLabel}
                </Button>
                {isBusy && <CircularProgress size={24} sx={{ alignSelf: { xs: 'center', sm: 'auto' } }} />}
            </Box>
        </Box>
    )
}
