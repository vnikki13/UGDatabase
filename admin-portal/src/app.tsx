import { GoogleOAuthProvider } from "@react-oauth/google"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import { useAuth } from "./auth"
import { routeTree } from "./routeTree.gen"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'; 

// Create a new router instance
const router = createRouter({
    routeTree, defaultPreload: 'intent',
    scrollRestoration: true,
    context: {
        auth: undefined!, // This will be set after we wrap the app in an AuthProvider
    },
})

// Register the router instance for type safety
declare module '@tanstack/react-router' {
    interface Register {
        router: typeof router
    }
}

// Register all AgGrid community features
ModuleRegistry.registerModules([AllCommunityModule]);

export function App() {
    const auth = useAuth()
    return (
        <>
            <GoogleOAuthProvider clientId={import.meta.env.VITE_GCS_CLIENT_ID}>
                <RouterProvider router={router} context={{ auth }} />
            </GoogleOAuthProvider>
            <ReactQueryDevtools initialIsOpen={false} />
        </>
    )
}