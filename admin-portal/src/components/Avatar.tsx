import { default as MUIAvatar } from "@mui/material/Avatar"
import { useAuth } from "../auth"

export function Avatar() {
    const { user } = useAuth()

    return user?.picture ? (
        <MUIAvatar alt={user.name} src={user.picture} />
    ) : (
        <MUIAvatar />
    )
}