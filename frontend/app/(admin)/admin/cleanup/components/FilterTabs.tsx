'use client'

import React from 'react'

export type FilterTab = 'priority' | 'cleanup' | 'duplicates' | 'all'

interface FilterTabsProps {
  activeTab: FilterTab
  counts: {
    priority: number
    cleanup: number
    duplicates: number
    all: number
  }
  onTabChange: (tab: FilterTab) => void
}

interface TabButtonProps {
  active: boolean
  onClick: () => void
  icon: string
  label: string
  count: number
}

function TabButton({ active, onClick, icon, label, count }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
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
      <div className="flex gap-1">
        <TabButton
          active={activeTab === 'priority'}
          onClick={() => onTabChange('priority')}
          icon="🎯"
          label="Priority Queue"
          count={counts.priority}
        />
        <TabButton
          active={activeTab === 'cleanup'}
          onClick={() => onTabChange('cleanup')}
          icon="🔧"
          label="Needs Cleanup"
          count={counts.cleanup}
        />
        <TabButton
          active={activeTab === 'duplicates'}
          onClick={() => onTabChange('duplicates')}
          icon="📋"
          label="Duplicates"
          count={counts.duplicates}
        />
        <TabButton
          active={activeTab === 'all'}
          onClick={() => onTabChange('all')}
          icon="📊"
          label="All Flags"
          count={counts.all}
        />
      </div>
    </div>
  )
}

// Tab filter configurations
export const TAB_FILTERS: Record<FilterTab, any> = {
  priority: { match_type: 'cross_dispensary', min_confidence: 0.7 },
  cleanup: { data_quality: 'poor,fair' },
  duplicates: { match_type: 'same_dispensary' },
  all: {},
}
