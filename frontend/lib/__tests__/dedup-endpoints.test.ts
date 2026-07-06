/**
 * Tests for the dedup admin endpoints (duplicate-scan, merge-batch,
 * duplicate_pair flag params) and the useDebounce hook.
 */
import MockAdapter from 'axios-mock-adapter'
import { renderHook, act } from '@testing-library/react'

jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    auth: {
      getSession: jest.fn(() => Promise.resolve({ data: { session: null }, error: null })),
      signOut: jest.fn(() => Promise.resolve({ error: null })),
    },
  })),
}))

jest.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(() => Promise.resolve({ data: { session: null }, error: null })),
      signOut: jest.fn(() => Promise.resolve({ error: null })),
    },
  },
}))

import { apiClient, api } from '../api'
import { useDebounce } from '../useDebounce'

describe('Dedup admin endpoints', () => {
  let mock: MockAdapter

  beforeEach(() => {
    mock = new MockAdapter(apiClient)
  })

  afterEach(() => {
    mock.restore()
  })

  it('duplicateScan POSTs to /api/admin/products/duplicate-scan', async () => {
    mock.onPost('/api/admin/products/duplicate-scan').reply(200, {
      total_pairs: 5, created: 3, skipped_existing: 2,
    })

    const res = await api.admin.quality.duplicateScan()
    expect(res.data.created).toBe(3)
    expect(mock.history.post).toHaveLength(1)
  })

  it('mergeBatch POSTs winner/loser/flag_id list', async () => {
    mock.onPost('/api/admin/products/merge-batch').reply(200, {
      merged: 1, failed: 0, results: [{ winner_id: 'w', loser_id: 'l', ok: true }],
    })

    await api.admin.quality.mergeBatch([
      { winner_id: 'w', loser_id: 'l', flag_id: 'f' },
    ])

    expect(mock.history.post).toHaveLength(1)
    expect(JSON.parse(mock.history.post[0].data)).toEqual({
      merges: [{ winner_id: 'w', loser_id: 'l', flag_id: 'f' }],
    })
  })

  it('flags.pending accepts duplicate_pair flag_type and skip', async () => {
    mock.onGet('/api/admin/flags/pending').reply(200, [])

    await api.admin.flags.pending({ flag_type: 'duplicate_pair', limit: 50, skip: 50 })

    expect(mock.history.get).toHaveLength(1)
    expect(mock.history.get[0].params).toEqual({
      flag_type: 'duplicate_pair', limit: 50, skip: 50,
    })
  })
})

describe('useDebounce', () => {
  beforeEach(() => jest.useFakeTimers())
  afterEach(() => jest.useRealTimers())

  it('only exposes the latest value after the delay elapses', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 400),
      { initialProps: { value: 'a' } }
    )

    expect(result.current).toBe('a')

    // Rapid keystrokes: value churns without the timer completing
    rerender({ value: 'ab' })
    act(() => { jest.advanceTimersByTime(200) })
    rerender({ value: 'abc' })
    act(() => { jest.advanceTimersByTime(200) })

    // Still the initial value — no 400ms quiet period yet
    expect(result.current).toBe('a')

    act(() => { jest.advanceTimersByTime(400) })
    expect(result.current).toBe('abc')
  })
})
