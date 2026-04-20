import { createFileRoute, redirect } from '@tanstack/react-router'
import LoginButton from '../components/LoginButton'
import { z } from 'zod'
import icon from '../assets/icon.png'

const fallback = '/dashboard' as const

export const Route = createFileRoute('/')({
  validateSearch: z.object({
    redirect: z.string().optional().catch(''),
  }),
  beforeLoad: ({ context, search }) => {
    if (context.auth.isAuthenticated) {
      throw redirect({ to: search.redirect || fallback })
    }
  },
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
      <img src={icon} alt="Ultrasound Guidance Logo" style={{ maxWidth: '200px', marginBottom: '2rem' }} />
      <h1>Ultrasound Guidance Admin Portal</h1>
      <LoginButton />
    </div>
  )
}
