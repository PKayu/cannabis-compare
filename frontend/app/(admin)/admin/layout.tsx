'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const tabs = [
  { href: '/admin', label: 'Dashboard' },
  { href: '/admin/cleanup', label: 'Cleanup Queue' },
  { href: '/admin/scrapers', label: 'Scrapers' },
  { href: '/admin/quality', label: 'Data Quality' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between py-4">
            <h1 className="text-xl font-bold text-gray-900">Admin Dashboard</h1>
            <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">
              Back to site
            </Link>
          </div>
          <nav className="flex gap-1 -mb-px">
            {tabs.map((tab) => {
              const isActive = pathname === tab.href
              return (
                <Link
                  key={tab.href}
                  href={tab.href}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    isActive
                      ? 'border-cannabis-600 text-cannabis-700'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 py-6">
        {children}
      </div>
    </div>
  )
}
