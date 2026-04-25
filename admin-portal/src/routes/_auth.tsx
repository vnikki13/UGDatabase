import { createFileRoute, Link as RouterLink, Outlet, redirect, useLocation } from '@tanstack/react-router'
import { Avatar } from '../components/Avatar'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Breadcrumbs from '@mui/material/Breadcrumbs'
import Divider from '@mui/material/Divider'
import Link from '@mui/material/Link'
import { Logo } from '../components/Logo'

const routeLabelMap: Record<string, string> = {
    dashboard: 'Dashboard',
    question: 'Question',
    exam: 'Exam',
}

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
    const location = useLocation()

    const pathSegments = location.pathname.split('/').filter(Boolean)
    const breadcrumbs = pathSegments.map((segment, index) => {
        const href = `/${pathSegments.slice(0, index + 1).join('/')}`
        const label = routeLabelMap[segment] ?? segment
        const isLast = index === pathSegments.length - 1

        return { href, label, isLast }
    })

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <AppBar position="static" color="transparent" elevation={0}>
                <Toolbar sx={{ gap: 2, minHeight: 72 }}>
                    <Box>
                        <Logo />
                    </Box>

                    <Typography
                        variant="h6"
                        component="h1"
                        sx={{ flexGrow: 1, textAlign: 'center' }}
                    >
                        Ultrasound Guidance Admin
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, md: 2 } }}>
                        <Avatar />
                    </Box>
                </Toolbar>
            </AppBar>

            <Box component="main" sx={{ flex: 1, px: { xs: 1, sm: 2, md: 4 }, pt: { xs: 1.5, sm: 2 }, pb: 4 }}>
                <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 3 }}>
                    <Link component={RouterLink} to="/dashboard" underline="hover" color="inherit">
                        Dashboard
                    </Link>
                    {breadcrumbs
                        .filter((crumb) => crumb.href !== '/dashboard')
                        .map((crumb) =>
                            crumb.isLast ? (
                                <Typography key={crumb.href} color="text.primary">
                                    {crumb.label}
                                </Typography>
                            ) : (
                                <Link
                                    key={crumb.href}
                                    component={RouterLink}
                                    to={crumb.href as '/dashboard' | '/question' | '/exam'}
                                    underline="hover"
                                    color="inherit"
                                >
                                    {crumb.label}
                                </Link>
                            ),
                        )}
                </Breadcrumbs>
                <Divider sx={{ mb: 3 }}
                />
                <Box sx={{ mt: 1 }}>
                    <Outlet />
                </Box>
            </Box>
        </Box>
    )

}
