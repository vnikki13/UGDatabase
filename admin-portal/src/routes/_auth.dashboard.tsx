import { createFileRoute } from '@tanstack/react-router'
import { useAuth } from '../auth'
import { Questions } from '../components/Questions'

export const Route = createFileRoute('/_auth/dashboard')({
    component: RouteComponent,
})

function RouteComponent() {
    const auth = useAuth()

    return (
        <section className="grid gap-2 p-2">
            <p>Hi {auth.user?.name}!</p>
            <p>You are currently on the dashboard route.</p>
            <Questions />
        </section>
    )
}
