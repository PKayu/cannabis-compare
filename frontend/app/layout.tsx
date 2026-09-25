import type { Metadata } from 'next'
import { Fredoka, Nunito, DM_Sans, Lobster } from 'next/font/google'
import './globals.css'
import AgeGateWrapper from './age-gate-wrapper'
import Navigation from '@/components/Navigation'
import Footer from '@/components/Footer'
import ComplianceBanner from '@/components/ComplianceBanner'
import { Providers } from './providers'
import { BRAND_NAME, BRAND_DESCRIPTION } from '@/lib/brand'

const dmSans = DM_Sans({ subsets: ['latin'], variable: '--font-dm-sans', display: 'swap' })
const lobster = Lobster({ subsets: ['latin'], weight: '400', variable: '--font-lobster', display: 'swap' })

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
  title: { default: BRAND_NAME, template: `%s | ${BRAND_NAME}` },
  description: BRAND_DESCRIPTION,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${fredoka.variable} ${nunito.variable} ${dmSans.variable} ${lobster.variable}`}>
      <body className="flex flex-col min-h-screen font-body bg-groovy-cream">
        <Providers>
          <AgeGateWrapper>
            <a className="bloom-skip" href="#main-content">Skip to content</a>
            <Navigation />
            <ComplianceBanner />
            <main id="main-content" tabIndex={-1} className="min-w-0 flex-1">
              {children}
            </main>
            <Footer />
          </AgeGateWrapper>
        </Providers>
      </body>
    </html>
  )
}
