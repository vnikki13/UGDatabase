import Button from "@mui/material/Button";
import { useAuth } from "../auth";
import { useRouter, useNavigate } from "@tanstack/react-router";

export function LogoutButton() {
    const { logout } = useAuth()
    const router = useRouter()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        router.invalidate()
        navigate({ to: '/' })
    }

    return <Button variant="contained" onClick={handleLogout}>Logout</Button>
}