import { useNavigate, useRouter } from '@tanstack/react-router'
import { type MouseEvent, useState } from 'react'
import MuiAvatar from '@mui/material/Avatar'
import IconButton from '@mui/material/IconButton'
import Menu from '@mui/material/Menu'
import MenuItem from '@mui/material/MenuItem'
import { useAuth } from '../auth'

export function Avatar() {
    const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null)
    const { user, logout } = useAuth()
    const router = useRouter()
    const navigate = useNavigate()

    const openMenu = (event: MouseEvent<HTMLElement>) => {
        setMenuAnchor(event.currentTarget)
    }

    const closeMenu = () => {
        setMenuAnchor(null)
    }

    const handleLogout = () => {
        closeMenu()
        logout()
        router.invalidate()
        navigate({ to: '/' })
    }

    return (
        <>
            <IconButton color="inherit" aria-label="open user menu" onClick={openMenu} sx={{ p: 0.5 }}>
                {user?.picture ? <MuiAvatar alt={user.name} src={user.picture} /> : <MuiAvatar />}
            </IconButton>

            <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={closeMenu}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </Menu>
        </>
    )
}