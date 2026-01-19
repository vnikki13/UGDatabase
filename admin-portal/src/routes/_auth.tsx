import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { Avatar } from '../components/Avatar'
import { LogoutButton } from '../components/LogoutButton'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

export const Route = createFileRoute('/_auth')({
    beforeLoad: ({ context }) => {
        if (!context.auth.isAuthenticated) {
            throw redirect({
                to: '/',
                search: {},
            })
        }
    },
    component: AuthLayout,
})

function AuthLayout() {
    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box
                component="header"
                sx={{
                    p: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    borderBottom: 1,
                    borderColor: 'divider'
                }}
            >
                <Typography variant="h5" component="h1">
                    Ultrasound Guidance Admin Dashboard
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar />
                    <LogoutButton />
                </Box>
            </Box>
            <Box component="main" sx={{ flex: 1, p: 2 }}>
                <Outlet />
            </Box>
        </Box>
    )

}
