import { createFileRoute } from '@tanstack/react-router'
import { Questions } from '../components/Questions'

export const Route = createFileRoute('/_auth/dashboard')({
    component: RouteComponent,
})

function RouteComponent() {
    return (
        <section className="grid gap-2 p-2">
            <Questions />
        </section>
    )
}
