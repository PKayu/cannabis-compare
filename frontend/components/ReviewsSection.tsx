'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/AuthContext'
import ReviewForm from './ReviewForm'

interface Review {
  id: string; rating: number; effects_rating: number | null; taste_rating: number | null
  value_rating: number | null; intention_type: string | null; intention_tag: string | null
  comment: string | null; upvotes: number; username: string; created_at: string; updated_at: string
}
export default function ReviewsSection({ productId }: { productId: string }) {
  const [reviews, setReviews] = useState<Review[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [showForm, setShowForm] = useState(false)
  const [filter, setFilter] = useState('')
  const [sort, setSort] = useState('recent')
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let current = true
    setStatus('loading')
    api.reviews.list(productId, { sort_by: sort, ...(filter ? { intention_tag: filter } : {}) }).then(response => {
      if (current) { setReviews(response.data); setStatus('ready') }
    }).catch(() => { if (current) setStatus('error') })
    return () => { current = false }
  }, [productId, filter, sort, retry])
  useEffect(() => { setShowForm(false) }, [productId])
  return <div className="bloom-panel p-5 sm:p-7">
    <div className="flex flex-wrap items-center justify-between gap-4"><h2 className="text-2xl font-bold">Community reviews</h2><button className="bloom-button-secondary" onClick={() => setShowForm(value => !value)} aria-expanded={showForm}>{showForm ? 'Close review form' : 'Write a review'}</button></div>
    <p className="mt-3 text-sm text-bloom-muted">Personal experiences, not medical advice. Sign in to share your own.</p>
    {showForm && <div className="bloom-review-form mt-6"><ReviewForm productId={productId} onSubmit={() => { setShowForm(false); setRetry(value => value + 1) }} onCancel={() => setShowForm(false)} /></div>}
    <div className="my-6 grid gap-4 sm:grid-cols-2">
      <label className="text-sm font-bold">Filter by reported use<select value={filter} className="bloom-input mt-2" onChange={event => setFilter(event.target.value)}>
        <option value="">All reviews</option><optgroup label="Medical">{[['pain','Pain relief'],['insomnia','Sleep / insomnia'],['anxiety','Anxiety'],['nausea','Nausea'],['spasms','Spasms']].map(([value,label]) => <option key={value} value={value}>{label}</option>)}</optgroup><optgroup label="Mood / wellness">{[['socializing','Socializing'],['creativity','Creativity'],['deep_relaxation','Deep relaxation'],['focus','Focus'],['post_workout','Post-workout']].map(([value,label]) => <option key={value} value={value}>{label}</option>)}</optgroup>
      </select></label>
      <label className="text-sm font-bold">Sort reviews<select className="bloom-input mt-2" value={sort} onChange={event => setSort(event.target.value)}><option value="recent">Most recent</option><option value="helpful">Most helpful</option><option value="rating_high">Highest rated</option></select></label>
    </div>
    {status === 'loading' ? <p role="status" className="py-8">Loading community reviews…</p>
      : status === 'error' ? <div role="alert"><p>Reviews could not be loaded.</p><button className="bloom-button-secondary mt-4" onClick={() => setRetry(value => value + 1)}>Retry reviews</button></div>
      : !reviews.length ? <p role="status" className="border-t border-bloom-line py-8 text-bloom-muted">{filter ? 'No reviews for this reported use. Choose all reviews to broaden the results.' : 'No reviews yet. Share your experience when you’re ready.'}</p>
      : <div className="divide-y divide-bloom-line">{reviews.map(review => <ReviewCard key={review.id} review={review} onUpvote={() => setRetry(value => value + 1)} />)}</div>}
  </div>
}
function ReviewCard({ review, onUpvote }: { review: Review; onUpvote: () => void }) {
  const { user, loading } = useAuth()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const upvote = async () => {
    if (!user) { setError('Sign in to mark this review as helpful.'); return }
    setBusy(true); setError('')
    try { await api.reviews.upvote(review.id); onUpvote() }
    catch { setError('Your vote could not be saved. Please try again.') }
    finally { setBusy(false) }
  }
  return <article className="py-6">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-bold">{review.username || 'Community member'}</h3><p className="text-xs text-bloom-muted">{new Date(review.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })}</p></div><p className="font-bold">{review.rating} / 5</p></div>
    <dl className="mt-4 flex flex-wrap gap-4 text-sm">{[['Effects', review.effects_rating], ['Taste', review.taste_rating], ['Value', review.value_rating]].map(([label,value]) => value != null && <div key={label as string} className="flex gap-1"><dt>{label}:</dt><dd className="font-bold">{value} / 5</dd></div>)}</dl>
    {review.intention_tag && <p className="mt-3 text-sm text-bloom-muted">Reported use: {review.intention_tag.replace(/_/g, ' ')}</p>}
    {review.comment && <p className="mt-3 whitespace-pre-wrap leading-relaxed">{review.comment}</p>}
    <button onClick={upvote} disabled={busy || loading} className="mt-3 min-h-[44px] rounded-lg px-3 text-sm font-bold underline disabled:opacity-60">{busy ? 'Saving vote…' : `Helpful (${review.upvotes})`}</button>
    {error && <p role="alert" className="text-sm text-bloom-error">{error}</p>}
  </article>
}
