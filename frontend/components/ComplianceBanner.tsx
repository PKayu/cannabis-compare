import CannabisLeaf from '@/components/CannabisLeaf'

export default function ComplianceBanner() {
  return (
    <aside className="compliance-banner" aria-label="Important site information">
      <div className="mx-auto flex max-w-7xl items-start gap-2 sm:items-center">
        <span aria-hidden="true" className="mt-0.5 sm:mt-0">
          <CannabisLeaf size={18} color="#1C1917" />
        </span>
        <p className="min-w-0 text-pretty">
          Informational purposes only. Utah Cannabis Compare does not sell controlled substances.
          Purchases take place on licensed dispensary websites. Utah medical cannabis cardholders 21+ only.
        </p>
      </div>
    </aside>
  )
}
