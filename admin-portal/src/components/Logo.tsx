import Box from "@mui/material/Box";
import icon from '../assets/icon.png'

export function Logo() {
    return (
        <Box
            component="img"
            src={icon}
            alt="Home"
            onClick={() => window.location.href = '/dashboard'}
            sx={{
                height: 100,
                cursor: 'pointer',
                padding: 2,
            }}
        />
    )
}