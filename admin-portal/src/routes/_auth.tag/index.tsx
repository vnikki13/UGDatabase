import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { AxiosError } from 'axios'
import { useAppForm } from '../../hooks/questionForm'
import { createTag } from '../../api'
import { FormActionFooter } from '../../components/FormActionFooter'
import { useQueryClient } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

export const Route = createFileRoute('/_auth/tag/')({
    component: RouteComponent,
})

function RouteComponent() {
    const queryClient = useQueryClient()
    const [submitSuccess, setSubmitSuccess] = useState(false)
    const [submitError, setSubmitError] = useState<string | null>(null)

    const form = useAppForm({
        defaultValues: { name: '' },
        onSubmit: async ({ value }) => {
            try {
                await createTag(value.name)
                await queryClient.invalidateQueries({ queryKey: ['tags'] })
                setSubmitSuccess(true)
                setSubmitError(null)
                form.reset()
            } catch (err: unknown) {
                setSubmitSuccess(false)
                if (err instanceof AxiosError) {
                    setSubmitError(err?.response?.data?.detail || 'Failed to create tag')
                } else if (err instanceof Error) {
                    setSubmitError(err.message)
                } else {
                    setSubmitError('Failed to create tag')
                }
            }
        },
    })

    return (
        <Box sx={{ maxWidth: 480 }}>
            <Typography variant="h5" component="h1" sx={{ mb: 3 }}>
                Create Tag
            </Typography>
            <form
                onSubmit={(e) => { e.preventDefault(); form.handleSubmit() }}
                onReset={() => form.reset()}
                autoComplete="off"
                noValidate
            >
                <form.AppField
                    name="name"
                    validators={{
                        onChange: ({ value }) => !value?.trim() ? 'Tag name is required' : undefined,
                        onSubmit: ({ value }) => !value?.trim() ? 'Tag name is required' : undefined,
                    }}
                    children={(field) => <field.TextField label="Tag Name" />}
                />
                <form.Subscribe
                    selector={(state) => [state.canSubmit, state.isSubmitting]}
                    children={([canSubmit, isSubmitting]) => (
                        <FormActionFooter
                            canSubmit={canSubmit as boolean}
                            isSubmitting={isSubmitting as boolean}
                            submitLabel="Create Tag"
                            successMessage={submitSuccess ? 'Tag created successfully!' : null}
                            errorMessage={submitError}
                            onCloseSuccess={() => setSubmitSuccess(false)}
                            onCloseError={() => setSubmitError(null)}
                        />
                    )}
                />
            </form>
        </Box>
    )
}

