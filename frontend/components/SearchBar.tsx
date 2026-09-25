'use client'

import { useEffect, useId, useState } from 'react'
import { api } from '@/lib/api'

interface Suggestion { id: string; name: string; brand: string | null; type: string }
export default function SearchBar({ onSearch, initialQuery = '' }: { onSearch: (query: string) => Promise<void> | void; initialQuery?: string }) {
  const [query, setQuery] = useState(initialQuery)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [show, setShow] = useState(false)
  const [active, setActive] = useState(-1)
  const [error, setError] = useState('')
  const id = useId()
  useEffect(() => { setQuery(initialQuery); setShow(false); setError('') }, [initialQuery])
  useEffect(() => {
    let current = true
    setSuggestions([]); setActive(-1)
    if (query.trim().length < 2) return
    const timer = setTimeout(async () => {
      try {
        const response = await api.products.autocomplete(query.trim())
        if (current) setSuggestions(response.data)
      } catch { if (current) setSuggestions([]) }
    }, 250)
    return () => { clearTimeout(timer); current = false }
  }, [query])
  const submit = (value: string) => {
    const trimmed = value.trim()
    if (trimmed.length < 2) { setError('Enter at least 2 characters to search.'); return }
    setQuery(trimmed); setShow(false); setError(''); void onSearch(trimmed)
  }
  return <form role="search" aria-label="Product search" className="relative" onSubmit={event => { event.preventDefault(); submit(query) }}>
    <label htmlFor={id} className="mb-2 block text-sm font-bold">Search products or brands</label>
    <div className="flex flex-col gap-3 sm:flex-row">
      <div className="relative min-w-0 flex-1">
        <input id={id} type="search" role="combobox" autoComplete="off" aria-autocomplete="list" aria-expanded={show && suggestions.length > 0} aria-controls={`${id}-suggestions`} aria-activedescendant={show && active >= 0 ? `${id}-option-${active}` : undefined} aria-describedby={`${id}-hint`} aria-invalid={Boolean(error)} value={query} onChange={event => { setQuery(event.target.value); setShow(true); setError('') }} onFocus={() => setShow(true)} onBlur={() => setShow(false)} placeholder="Try a product name or brand" className="bloom-input h-14" onKeyDown={event => {
          if (event.key === 'Escape') { setShow(false); setActive(-1) }
          if (suggestions.length && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) { event.preventDefault(); setShow(true); setActive(index => event.key === 'ArrowDown' ? (index + 1) % suggestions.length : (index - 1 + suggestions.length) % suggestions.length) }
          if (event.key === 'Enter' && show && active >= 0 && suggestions[active]) { event.preventDefault(); submit(suggestions[active].name) }
        }} />
        <ul id={`${id}-suggestions`} role="listbox" aria-label="Product suggestions" hidden={!show || !suggestions.length} className="absolute top-full z-20 mt-2 max-h-72 w-full overflow-y-auto rounded-xl border border-bloom-line bg-bloom-cream shadow-lg">
          {suggestions.map((suggestion, index) => <li id={`${id}-option-${index}`} key={suggestion.id} role="option" aria-selected={active === index} onMouseDown={event => event.preventDefault()} onClick={() => submit(suggestion.name)} className={`cursor-pointer px-4 py-3 ${active === index ? 'bg-bloom-parchment' : 'hover:bg-bloom-parchment'}`}><span className="block font-bold">{suggestion.name}</span><span className="text-sm text-bloom-muted">{suggestion.brand ?? 'Brand not reported'} · {suggestion.type}</span></li>)}
        </ul>
      </div>
      <button className="bloom-button min-h-14 sm:px-8" type="submit">Search</button>
    </div>
    <p id={`${id}-hint`} className={`mt-2 text-sm ${error ? 'text-bloom-error' : 'text-bloom-muted'}`} role={error ? 'alert' : undefined}>{error || 'Start with 2 or more characters. Filter your results below.'}</p>
  </form>
}
