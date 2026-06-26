import type { Metadata } from 'next'
import { Fredoka, Nunito } from 'next/font/google'
import './globals.css'
import AgeGateWrapper from './age-gate-wrapper'
import Navigation from '@/components/Navigation'
import Footer from '@/components/Footer'
import { Providers } from './providers'

const fredoka = Fredoka({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-fredoka',
  display: 'swap',
})

const nunito = Nunito({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-nunito',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Utah Cannabis Compare',
  description: 'Compare prices and read reviews for cannabis products across Utah dispensaries',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${fredoka.variable} ${nunito.variable}`}>
      <body className="flex flex-col min-h-screen font-body bg-groovy-cream">
        <Providers>
          <AgeGateWrapper>
            <Navigation />
            <main className="flex-1">
              {children}
            </main>
            <Footer />
          </AgeGateWrapper>
        </Providers>
      </body>
    </html>
  )
}
