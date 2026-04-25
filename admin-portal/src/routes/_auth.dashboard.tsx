import { createFileRoute } from '@tanstack/react-router'
import { Questions } from '../components/Questions'
import { Exams } from '../components/Exams'
import Box from '@mui/material/Box'

export const Route = createFileRoute('/_auth/dashboard')({
    component: RouteComponent,
})

function RouteComponent() {
    return (
        <Box>
            <Box sx={{ mb: 6 }}>
                <Questions />
            </Box>
            <Exams />
        </Box>
    )
}
