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
                height: { xs: 60, sm: 80, md: 100 },
                width: 'auto',
                cursor: 'pointer',
                padding: { xs: 0.5, sm: 1, md: 2 },
            }}
        />
    )
}