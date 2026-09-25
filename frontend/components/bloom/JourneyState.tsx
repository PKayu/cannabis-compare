import type { ReactNode } from 'react'

export default function JourneyState({ title, children, busy = false, error = false }: { title: string; children?: ReactNode; busy?: boolean; error?: boolean }) {
  return <div className="bloom-panel px-6 py-12 sm:px-10" role={error ? 'alert' : 'status'}>
    {busy && <div aria-hidden="true" className="mb-6 h-2 w-24 animate-pulse rounded-full bg-bloom-avocado" />}
    <h2 className="text-2xl font-bold">{title}</h2>
    <div className="mt-3 max-w-xl text-bloom-muted">{children}</div>
  </div>
}
