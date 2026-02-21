'use client'

import React from 'react'

export type FilterTab = 'priority' | 'cleanup' | 'duplicates' | 'auto_linked' | 'all'

interface FilterTabsProps {
  activeTab: FilterTab
  counts: {
    priority: number
    cleanup: number
    duplicates: number
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
          active={activeTab === 'priority'}
          onClick={() => onTabChange('priority')}
          icon="🎯"
          label="Priority Queue"
          description="Link the same product found at different dispensaries"
          count={counts.priority}
        />
        <TabButton
          active={activeTab === 'cleanup'}
          onClick={() => onTabChange('cleanup')}
          icon="🔧"
          label="Needs Cleanup"
          description="Fix dirty product data — edit name, category, brand, then save as new product"
          count={counts.cleanup}
        />
        <TabButton
          active={activeTab === 'duplicates'}
          onClick={() => onTabChange('duplicates')}
          icon="📋"
          label="Duplicates"
          description="Same-dispensary duplicates — pick which one to keep and merge the other"
          count={counts.duplicates}
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
          description="All flags including good-quality products for verification"
          count={counts.all}
        />
      </div>

      {/* Tab context hint */}
      <div className="px-1 pb-2 pt-1">
        {activeTab === 'priority' && (
          <p className="text-xs text-blue-600">
            These products were scraped from one dispensary and likely match a product at another. Approve to link them, or create a new product.
          </p>
        )}
        {activeTab === 'cleanup' && (
          <p className="text-xs text-orange-600">
            These products have dirty or missing data. Edit the name, category, and other fields — then save as &quot;New Product&quot;. No linking needed here.
          </p>
        )}
        {activeTab === 'duplicates' && (
          <p className="text-xs text-yellow-700">
            Same dispensary has two entries that look like the same product. Use &quot;Keep This One&quot; to merge the duplicate into the winner.
          </p>
        )}
        {activeTab === 'auto_linked' && (
          <p className="text-xs text-purple-600">
            These products were automatically linked at &gt;90% confidence. Spot-check to make sure the auto-merge was correct.
          </p>
        )}
        {activeTab === 'all' && (
          <p className="text-xs text-gray-500">
            All flags. Use the Advanced Filters to narrow by quality, dispensary, or confidence. Check &quot;Good Quality&quot; to verify clean products.
          </p>
        )}
      </div>
    </div>
  )
}

// Tab filter configurations
export const TAB_FILTERS: Record<FilterTab, any> = {
  priority: { match_type: 'cross_dispensary' },
  cleanup: { data_quality: 'poor,fair' },
  duplicates: { match_type: 'same_dispensary' },
  auto_linked: { include_auto_merged: true },
  all: {},
}
