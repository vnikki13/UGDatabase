import { createFileRoute } from '@tanstack/react-router'
import LoginButton from '../components/LoginButton'

export const Route = createFileRoute('/')({
    component: Index,
})

function Index() {
    return (
        <div className="p-2">
            <h2>Welcome Nikki!</h2>
            <LoginButton />
        </div>
    )
}
