import { useQuery } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import Chip from '@mui/material/Chip'
import Divider from '@mui/material/Divider'
import { getAuditHistory } from '../api'
import type { AuditEvent } from '../types'

interface AuditHistoryProps {
    entityType: string
    entityId: string
}

const LOCAL_TIME_ZONE = Intl.DateTimeFormat().resolvedOptions().timeZone

function formatAction(action: string): string {
    return action.replace(/\./g, ' › ')
}

function formatDate(iso: string): string {
    const date = new Date(iso)
    if (Number.isNaN(date.getTime())) {
        return iso
    }

    return new Intl.DateTimeFormat(undefined, {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: 'numeric',
        minute: '2-digit',
        timeZone: LOCAL_TIME_ZONE,
        timeZoneName: 'short',
    }).format(date)
}

function ActionChip({ action }: { action: string }) {
    const color = action.includes('delete')
        ? 'error'
        : action.includes('create')
            ? 'success'
            : 'default'
    return <Chip label={formatAction(action)} color={color} size="small" />
}

function AuditRow({ event }: { event: AuditEvent }) {
    return (
        <Box sx={{ py: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <ActionChip action={event.action} />
                <Typography variant="body2" color="text.secondary">
                    {formatDate(event.occurred_at)}
                </Typography>
                {event.actor_email && (
                    <Typography variant="body2" color="text.secondary">
                        by <strong>{event.actor_email}</strong>
                    </Typography>
                )}
            </Box>
        </Box>
    )
}

export function AuditHistory({ entityType, entityId }: AuditHistoryProps) {
    const { data, isLoading, error } = useQuery<AuditEvent[]>({
        queryKey: ['audit-history', entityType, entityId],
        queryFn: () => getAuditHistory(entityType, entityId),
    })

    return (
        <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
                History
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Times shown in your local timezone ({LOCAL_TIME_ZONE})
            </Typography>
            <Divider sx={{ mb: 1 }} />
            {isLoading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                    <CircularProgress size={24} />
                </Box>
            )}
            {error && (
                <Typography variant="body2" color="error">
                    Failed to load history.
                </Typography>
            )}
            {data && data.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                    No history recorded yet.
                </Typography>
            )}
            {data && data.map((event) => (
                <Box key={event.id}>
                    <AuditRow event={event} />
                    <Divider />
                </Box>
            ))}
        </Box>
    )
}
