import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { Avatar } from '../components/Avatar'
import { LogoutButton } from '../components/LogoutButton'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { Logo } from '../components/Logo'

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
                <Logo />
                <Typography variant="h5" component="h1" style={{textAlign: 'center'}}>
                    Ultrasound Guidance Admin Dashboard
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, padding: 2 }}>
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
