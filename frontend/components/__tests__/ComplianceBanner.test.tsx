import { render, screen } from '@testing-library/react'
import ComplianceBanner from '../ComplianceBanner'

describe('ComplianceBanner', () => {
  it('states the informational, no-sale, external-purchase, and age requirements', () => {
    render(<ComplianceBanner />)

    const notice = screen.getByRole('complementary', { name: /important site information/i })

    expect(notice).toHaveTextContent(/informational purposes only/i)
    expect(notice).toHaveTextContent(/does not sell controlled substances/i)
    expect(notice).toHaveTextContent(/licensed dispensary websites/i)
    expect(notice).toHaveTextContent(/cardholders 21\+ only/i)
  })
})
