import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { AxiosError } from 'axios'
import { useAppForm } from '../../hooks/questionForm'
import { getTagById, updateTag, deleteTag } from '../../api'
import { FormActionFooter } from '../../components/FormActionFooter'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogContentText from '@mui/material/DialogContentText'
import DialogActions from '@mui/material/DialogActions'
import type { TagWithId } from '../../types'
import { useAuth } from '../../auth'
import { AuditHistory } from '../../components/AuditHistory'

export const Route = createFileRoute('/_auth/tag/$tagId')({
    component: RouteComponent,
})

function RouteComponent() {
    const { tagId } = Route.useParams()
    const { user } = useAuth()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [submitSuccess, setSubmitSuccess] = useState(false)
    const [submitError, setSubmitError] = useState<string | null>(null)
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
    const [isDeleting, setIsDeleting] = useState(false)

    const { data: tag, isLoading } = useQuery<TagWithId>({
        queryKey: ['tag', tagId],
        queryFn: () => getTagById(tagId),
    })

    const form = useAppForm({
        defaultValues: { name: tag?.name ?? '' },
        onSubmit: async ({ value }) => {
            try {
                await updateTag(tagId, value.name, user?.email)
                await queryClient.invalidateQueries({ queryKey: ['tags'] })
                await queryClient.invalidateQueries({ queryKey: ['tag', tagId] })
                setSubmitSuccess(true)
                setSubmitError(null)
            } catch (err: unknown) {
                setSubmitSuccess(false)
                if (err instanceof AxiosError) {
                    setSubmitError(err?.response?.data?.detail || 'Failed to update tag')
                } else if (err instanceof Error) {
                    setSubmitError(err.message)
                } else {
                    setSubmitError('Failed to update tag')
                }
            }
        },
    })

    if (isLoading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                <CircularProgress />
            </Box>
        )
    }

    const handleDelete = async () => {
        setIsDeleting(true)
        try {
            await deleteTag(tagId, user?.email)
            await queryClient.invalidateQueries({ queryKey: ['tags'] })
            navigate({ to: '/dashboard' })
        } catch (err: unknown) {
            setDeleteDialogOpen(false)
            setIsDeleting(false)
            if (err instanceof Error) {
                setSubmitError(err.message)
            } else {
                setSubmitError('Failed to delete tag')
            }
        }
    }

    return (
        <Box sx={{ maxWidth: 480 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" component="h1">
                    Edit Tag
                </Typography>
                <Button
                    variant="outlined"
                    color="error"
                    onClick={() => setDeleteDialogOpen(true)}
                >
                    Delete Tag
                </Button>
            </Box>
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
                            submitLabel="Save Changes"
                            successMessage={submitSuccess ? 'Tag updated successfully!' : null}
                            errorMessage={submitError}
                            onCloseSuccess={() => setSubmitSuccess(false)}
                            onCloseError={() => setSubmitError(null)}
                        />
                    )}
                />
            </form>

            <Dialog open={deleteDialogOpen} onClose={() => !isDeleting && setDeleteDialogOpen(false)}>
                <DialogTitle>Delete Tag</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Are you sure you want to delete <strong>{tag?.name}</strong>? This tag will no longer appear in the tag list, but existing questions that use it will keep their association.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)} disabled={isDeleting}>
                        Cancel
                    </Button>
                    <Button onClick={handleDelete} color="error" variant="contained" loading={isDeleting}>
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>

            <AuditHistory entityType="tag" entityId={tagId} />
        </Box>
    )
}

