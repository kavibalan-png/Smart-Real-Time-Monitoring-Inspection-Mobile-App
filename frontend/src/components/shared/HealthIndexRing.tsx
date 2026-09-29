/**
 * Health Index Ring — circular visualization with score and status.
 * Labeled "Composite Monitoring Health Index — Prototype"
 */
import React from 'react'
import clsx from 'clsx'

interface Props {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

function getStatusInfo(score: number) {
  if (score >= 80) return { label: 'HEALTHY', color: '#16a34a', ring: '#dcfce7' }
  if (score >= 65) return { label: 'WATCH', color: '#d97706', ring: '#fef3c7' }
  if (score >= 45) return { label: 'HIGH ATTENTION', color: '#ea580c', ring: '#ffedd5' }
  return { label: 'CRITICAL', color: '#dc2626', ring: '#fee2e2' }
}

const SIZES = {
  sm: { r: 28, stroke: 5, font: 'text-xl', sub: 'text-xs' },
  md: { r: 42, stroke: 7, font: 'text-3xl', sub: 'text-sm' },
  lg: { r: 56, stroke: 9, font: 'text-4xl', sub: 'text-base' },
}

export function HealthIndexRing({ score, size = 'md', showLabel = true }: Props) {
  const { r, stroke, font, sub } = SIZES[size]
  const cx = r + stroke
  const cy = r + stroke
  const svgSize = (r + stroke) * 2
  const circumference = 2 * Math.PI * r
  const progress = Math.max(0, Math.min(100, score))
  const dashOffset = circumference - (progress / 100) * circumference
  const { label, color, ring } = getStatusInfo(score)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative inline-flex items-center justify-center">
        <svg
          width={svgSize}
          height={svgSize}
          aria-label={`Health index: ${score}/100 — ${label}`}
        >
          {/* Background ring */}
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={ring}
            strokeWidth={stroke}
          />
          {/* Progress ring */}
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            transform={`rotate(-90 ${cx} ${cy})`}
            style={{ transition: 'stroke-dashoffset 0.8s ease-in-out' }}
          />
        </svg>
        <div className="absolute flex flex-col items-center leading-none">
          <span className={clsx('font-bold', font)} style={{ color }}>
            {Math.round(score)}
          </span>
          <span className={clsx('text-slate-500', sub)}>/ 100</span>
        </div>
      </div>
      {showLabel && (
        <div className="text-center">
          <span
            className="text-xs font-bold uppercase tracking-wide px-2 py-0.5 rounded-full"
            style={{ color, backgroundColor: ring }}
          >
            {label}
          </span>
        </div>
      )}
    </div>
  )
}
