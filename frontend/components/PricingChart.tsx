'use client'

import { useEffect, useId, useState } from 'react'
import { api } from '@/lib/api'
import { money, type PriceHistoryPoint } from '@/lib/product-contracts'

export default function PricingChart({ productId }: { productId: string }) {
  const [history, setHistory] = useState<PriceHistoryPoint[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [days, setDays] = useState(30)
  const [retry, setRetry] = useState(0)
  const id = useId()
  useEffect(() => {
    let current = true
    setStatus('loading')
    api.products.getPricingHistory(productId, days).then(response => {
      if (current) { setHistory(response.data); setStatus('ready') }
    }).catch(() => { if (current) setStatus('error') })
    return () => { current = false }
  }, [productId, days, retry])

  const low = history.length ? Math.min(...history.map(point => point.min)) : 0
  const high = history.length ? Math.max(...history.map(point => point.max)) : 0
  const range = high - low || 1
  const x = (index: number) => 65 + index * 610 / Math.max(history.length - 1, 1)
  const y = (price: number) => 170 - (price - low) * 135 / range
  const date = (value: string) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })
  return <div className="bloom-panel p-5 sm:p-7">
    <div className="flex flex-wrap items-center justify-between gap-4">
      <h2 className="text-2xl font-bold">Price observations</h2>
      <label className="flex items-center gap-3 text-sm font-bold">Period
        <select className="bloom-input w-auto" value={days} onChange={event => setDays(Number(event.target.value))}><option value={7}>7 days</option><option value={30}>30 days</option><option value={90}>90 days</option></select>
      </label>
    </div>
    <p className="mt-3 max-w-2xl text-sm text-bloom-muted">Listed prices across all package sizes, grouped by last update date. These are observations, not a complete price-change history or a like-for-like trend. Promotions are not included.</p>
    {status === 'loading' ? <p role="status" className="py-10">Loading price observations…</p>
      : status === 'error' ? <div role="alert" className="py-6"><p>Price observations could not be loaded. Current offers are still available above.</p><button className="bloom-button-secondary mt-4" onClick={() => setRetry(value => value + 1)}>Retry price observations</button></div>
      : history.length === 0 ? <p role="status" className="py-8 text-bloom-muted">No price observations in this period. Try a longer period or compare current offers.</p>
      : <>
        <p className="mt-5 text-sm tabular-nums sm:hidden">Observed range: <strong>{money(low)}–{money(high)}</strong>. Open the price data below for each date.</p>
        {history.length > 1 ? <svg viewBox="0 0 720 215" role="img" aria-labelledby={`${id}-title ${id}-desc`} className="mt-6 hidden w-full sm:block">
          <title id={`${id}-title`}>Daily listed price ranges</title>
          <desc id={`${id}-desc`}>Vertical bars show each day&apos;s low and high. The solid line shows daily averages. Exact values follow in the data table.</desc>
          <text x="0" y="40" fontSize="14" fill="currentColor">{money(high)}</text><text x="0" y="174" fontSize="14" fill="currentColor">{money(low)}</text>
          <line x1="65" x2="690" y1="170" y2="170" stroke="#CBD2C7" />
          {history.map((point, index) => <line key={point.date} x1={x(index)} x2={x(index)} y1={y(point.min)} y2={y(point.max)} stroke="#49616A" strokeWidth="4" />)}
          <polyline fill="none" stroke="#103D50" strokeWidth="3" points={history.map((point, index) => `${x(index)},${y(point.avg)}`).join(' ')} />
          {history.map((point, index) => <circle key={point.date} cx={x(index)} cy={y(point.avg)} r="4" fill="#103D50" />)}
          <text x="65" y="205" fontSize="14" fill="currentColor">{date(history[0].date)}</text><text x="675" y="205" textAnchor="end" fontSize="14" fill="currentColor">{date(history[history.length - 1].date)}</text>
        </svg> : <p className="mt-6">Only one observation date is available; not enough to show change over time.</p>}
        <details className="mt-5">
          <summary className="min-h-[44px] cursor-pointer py-3 font-bold underline underline-offset-4">View price data ({history.length} dates)</summary>
          <div className="overflow-x-auto" role="region" aria-label="Price observation data" tabIndex={0}>
            <table className="w-full text-left text-sm tabular-nums"><caption className="sr-only">Listed prices by update date, all package sizes</caption><thead><tr>{['Date', 'Low', 'Average', 'High'].map(label => <th key={label} scope="col" className="py-3 pr-3">{label}</th>)}</tr></thead><tbody>
              {history.map(point => <tr key={point.date} className="border-t border-bloom-line"><th scope="row" className="py-3 pr-3 font-normal">{date(point.date)}</th><td className="pr-3">{money(point.min)}</td><td className="pr-3">{money(point.avg)}</td><td>{money(point.max)}</td></tr>)}
            </tbody></table>
          </div>
        </details>
      </>}
  </div>
}
