'use client'

import React from 'react'

export type FilterTab = 'data_cleanup' | 'legacy_review' | 'auto_linked' | 'all'

interface FilterTabsProps {
  activeTab: FilterTab
  counts: {
    data_cleanup: number
    legacy_review: number
    auto_linked: number
    all: number
  }
  onTabChange: (tab: FilterTab) => void
}

interface TabButtonProps {
  active: boolean
  onClick: () => void
  icon: string
  label: string
  description: string
  count: number
}

function TabButton({ active, onClick, icon, label, description, count }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      title={description}
      className={`
        flex items-center gap-2 px-4 py-2 rounded-t-lg border-b-2 transition-colors
        ${active
          ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium'
          : 'border-transparent hover:bg-gray-100 text-gray-600'
        }
      `}
    >
      <span className="text-lg">{icon}</span>
      <span>{label}</span>
      <span
        className={`
          ml-1 px-2 py-0.5 rounded-full text-xs font-medium
          ${active ? 'bg-blue-200 text-blue-800' : 'bg-gray-200 text-gray-700'}
        `}
      >
        {count}
      </span>
    </button>
  )
}

export function FilterTabs({ activeTab, counts, onTabChange }: FilterTabsProps) {
  return (
    <div className="border-b border-gray-200 mb-6">
      <div className="flex flex-wrap gap-1">
        <TabButton
          active={activeTab === 'data_cleanup'}
          onClick={() => onTabChange('data_cleanup')}
          icon="🔧"
          label="Data Cleanup"
          description="Fix dirty product data — edit fields, then activate the product"
          count={counts.data_cleanup}
        />
        <TabButton
          active={activeTab === 'legacy_review'}
          onClick={() => onTabChange('legacy_review')}
          icon="🔗"
          label="Legacy Reviews"
          description="Old-style match review flags — approve, reject, or dismiss"
          count={counts.legacy_review}
        />
        <TabButton
          active={activeTab === 'auto_linked'}
          onClick={() => onTabChange('auto_linked')}
          icon="⚡"
          label="Auto-Linked"
          description="Products auto-merged at >90% confidence — spot-check these"
          count={counts.auto_linked}
        />
        <TabButton
          active={activeTab === 'all'}
          onClick={() => onTabChange('all')}
          icon="📊"
          label="All Flags"
          description="All flags for audit purposes"
          count={counts.all}
        />
      </div>

      {/* Tab context hint */}
      <div className="px-1 pb-2 pt-1">
        {activeTab === 'data_cleanup' && (
          <p className="text-xs text-orange-600">
            These products were imported with dirty data. Edit the fields to fix them, then &quot;Save &amp; Activate&quot; to make them live. Or &quot;Delete&quot; if the data is garbage.
          </p>
        )}
        {activeTab === 'legacy_review' && (
          <p className="text-xs text-blue-600">
            These flags were created before the scoring overhaul (when 60–90% matches were flagged for review). New scrapes will <strong>not</strong> generate these — only cross-dispensary auto-merges at &gt;90% go to Auto-Linked now. Clear this backlog at your own pace.
          </p>
        )}
        {activeTab === 'auto_linked' && (
          <p className="text-xs text-purple-600">
            These products were automatically linked at &gt;90% confidence. Spot-check to make sure the auto-merge was correct.
          </p>
        )}
        {activeTab === 'all' && (
          <p className="text-xs text-gray-500">
            All flags across all types. Use this view for auditing.
          </p>
        )}
      </div>
    </div>
  )
}

// Tab filter configurations — sent as query params to the pending flags API
export const TAB_FILTERS: Record<FilterTab, any> = {
  data_cleanup: { flag_type: 'data_cleanup' },
  legacy_review: { flag_type: 'match_review' },
  auto_linked: { include_auto_merged: true },
  all: {},
}
