import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Utah Cannabis Aggregator',
  description: 'Compare prices and read reviews for cannabis products across Utah dispensaries',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
