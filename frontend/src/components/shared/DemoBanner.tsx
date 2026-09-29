/**
 * Demo/Prototype banner — clearly labels synthetic data.
 * Required by PS guidelines: never hide demo status.
 */
import React from 'react'
import { FlaskConical } from 'lucide-react'

interface Props {
  message?: string
  inline?: boolean
}

export function DemoBanner({
  message = 'Composite Monitoring Health Index — Prototype | Synthetic demo data — not official government data',
  inline = false,
}: Props) {
  if (inline) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full font-medium">
        <FlaskConical className="w-3 h-3" aria-hidden />
        DEMO
      </span>
    )
  }

  return (
    <div
      className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-md px-3 py-2 text-xs text-amber-800"
      role="note"
      aria-label="Demo data notice"
    >
      <FlaskConical className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" aria-hidden />
      <span className="font-medium">{message}</span>
    </div>
  )
}
