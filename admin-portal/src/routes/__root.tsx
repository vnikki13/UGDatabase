import { createRootRouteWithContext, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import type { AuthContext } from '../auth'

interface RouterContext {
    auth: AuthContext
}

const RootLayout = () => (
    <>
        <Outlet />
        <TanStackRouterDevtools />
    </>
)

export const Route = createRootRouteWithContext<RouterContext>()({ component: RootLayout })
