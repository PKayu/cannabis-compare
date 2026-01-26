import type { Metadata } from 'next'
import './globals.css'
import AgeGateWrapper from './age-gate-wrapper'
import Navigation from '@/components/Navigation'

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
      <body>
        <AgeGateWrapper>
          <Navigation />
          {children}
        </AgeGateWrapper>
      </body>
    </html>
  )
}
