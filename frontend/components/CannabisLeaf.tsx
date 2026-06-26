import React from 'react'

interface CannabisLeafProps {
  size?: number
  color?: string
  className?: string
  variant?: 'leaf' | 'sprig' | 'stalk'
  rotate?: number
}

export default function CannabisLeaf({
  size = 48,
  color = '#0F766E',
  className = '',
  variant = 'leaf',
  rotate = 0,
}: CannabisLeafProps) {
  const style: React.CSSProperties = {
    width: size,
    height: size,
    transform: rotate ? `rotate(${rotate}deg)` : undefined,
    flexShrink: 0,
  }

  if (variant === 'sprig') {
    return (
      <svg style={style} className={className} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Simple botanical sprig — stem with small oval leaves */}
        <line x1="24" y1="44" x2="24" y2="8" stroke={color} strokeWidth="2.5" strokeLinecap="round"/>
        <ellipse cx="24" cy="22" rx="9" ry="5" fill={color} transform="rotate(-35 24 22)"/>
        <ellipse cx="24" cy="22" rx="9" ry="5" fill={color} transform="rotate(35 24 22)"/>
        <ellipse cx="24" cy="12" rx="7" ry="4" fill={color} transform="rotate(-25 24 12)"/>
        <ellipse cx="24" cy="12" rx="7" ry="4" fill={color} transform="rotate(25 24 12)"/>
        <ellipse cx="24" cy="8" rx="5" ry="3" fill={color}/>
      </svg>
    )
  }

  if (variant === 'stalk') {
    return (
      <svg style={style} className={className} viewBox="0 0 48 64" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Hemp stalk with pairs of serrated leaves */}
        <line x1="24" y1="62" x2="24" y2="4" stroke={color} strokeWidth="3" strokeLinecap="round"/>
        {/* Leaf pair 1 - bottom */}
        <path d="M24 50 Q14 44 10 36 Q18 38 24 50Z" fill={color}/>
        <path d="M24 50 Q34 44 38 36 Q30 38 24 50Z" fill={color}/>
        {/* Leaf pair 2 - middle */}
        <path d="M24 36 Q11 28 7 18 Q17 22 24 36Z" fill={color}/>
        <path d="M24 36 Q37 28 41 18 Q31 22 24 36Z" fill={color}/>
        {/* Leaf pair 3 - upper */}
        <path d="M24 22 Q14 16 12 8 Q20 11 24 22Z" fill={color}/>
        <path d="M24 22 Q34 16 36 8 Q28 11 24 22Z" fill={color}/>
        {/* Top bud */}
        <ellipse cx="24" cy="6" rx="4" ry="5" fill={color}/>
      </svg>
    )
  }

  // Default: stylized cannabis leaf (5-finger fan)
  return (
    <svg style={style} className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Center stem */}
      <line x1="32" y1="60" x2="32" y2="32" stroke={color} strokeWidth="2.5" strokeLinecap="round"/>
      {/* Center finger — tall middle */}
      <path
        d="M32 32 C30 26 27 18 28 8 C30 12 32 16 32 16 C32 16 34 12 36 8 C37 18 34 26 32 32Z"
        fill={color}
      />
      {/* Left-center finger */}
      <path
        d="M32 34 C26 30 18 28 10 24 C14 26 18 30 20 32 C20 32 18 34 16 34 C22 36 28 36 32 34Z"
        fill={color}
      />
      {/* Right-center finger */}
      <path
        d="M32 34 C38 30 46 28 54 24 C50 26 46 30 44 32 C44 32 46 34 48 34 C42 36 36 36 32 34Z"
        fill={color}
      />
      {/* Far-left finger */}
      <path
        d="M30 36 C24 34 14 36 6 30 C10 30 14 32 16 34 C14 36 12 38 12 40 C18 38 26 38 30 36Z"
        fill={color}
      />
      {/* Far-right finger */}
      <path
        d="M34 36 C40 34 50 36 58 30 C54 30 50 32 48 34 C50 36 52 38 52 40 C46 38 38 38 34 36Z"
        fill={color}
      />
      {/* Stem root */}
      <path d="M30 58 C30 54 28 52 28 50 C30 52 32 54 32 56 C32 54 34 52 36 50 C36 52 34 54 34 58Z" fill={color}/>
    </svg>
  )
}

/* Scatter layout helper — places multiple leaves decoratively */
export function LeafCluster({ color = '#0F766E', className = '' }: { color?: string; className?: string }) {
  return (
    <div className={`relative pointer-events-none select-none ${className}`}>
      <CannabisLeaf size={40} color={color} rotate={-20} className="absolute -top-2 -left-4 opacity-60" />
      <CannabisLeaf size={28} color={color} rotate={15} variant="sprig" className="absolute top-4 left-8 opacity-40" />
      <CannabisLeaf size={32} color={color} rotate={-45} className="absolute top-0 left-14 opacity-50" />
    </div>
  )
}
