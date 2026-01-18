import { createFileRoute, redirect } from '@tanstack/react-router'
import LoginButton from '../components/LoginButton'
import { z } from 'zod'

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
    <>
      <h2>Login page</h2>
      <LoginButton />
    </>
  )
}
