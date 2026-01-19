import Box from "@mui/material/Box";

export function Logo() {
    return (
        <Box
            component="img"
            src="/src/assets/icon.png"
            alt="Home"
            onClick={() => window.location.href = '/dashboard'}
            sx={{
                height: 100,
                cursor: 'pointer'
            }}
        />
    )
}