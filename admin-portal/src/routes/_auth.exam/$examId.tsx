import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_auth/exam/$examId')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/_auth/exam/$examId"!</div>
}
