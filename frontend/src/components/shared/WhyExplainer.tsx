/**
 * WHY Explainer Component — signature feature.
 * Every AI/analytics output surfaces its reasoning here.
 */
import React, { useState } from 'react'
import { ChevronDown, ChevronUp, HelpCircle, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

interface Reason {
  label: string
  score?: number
  evidence?: string
  threshold?: string
}

interface Props {
  title?: string
  reasons: Reason[]
  disclaimer?: string
  methodology?: string
  triggerLabel?: string
  variant?: 'anomaly' | 'health' | 'assignment' | 'inspection'
  className?: string
}

const VARIANT_STYLES = {
  anomaly: 'border-orange-200 bg-orange-50',
  health: 'border-blue-200 bg-blue-50',
  assignment: 'border-teal-200 bg-teal-50',
  inspection: 'border-slate-200 bg-slate-50',
}

export function WhyExplainer({
  title = 'WHY?',
  reasons,
  disclaimer,
  methodology,
  triggerLabel = 'WHY THIS?',
  variant = 'anomaly',
  className,
}: Props) {
  const [expanded, setExpanded] = useState(false)

  if (reasons.length === 0) return null

  return (
    <div className={clsx('rounded-lg border', VARIANT_STYLES[variant], className)}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-white/50 transition-colors rounded-lg"
        aria-expanded={expanded}
        aria-controls="why-content"
      >
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-slate-600" aria-hidden />
          <span className="text-sm font-semibold text-slate-700">{triggerLabel}</span>
          <span className="text-xs text-slate-500">({reasons.length} reason{reasons.length !== 1 ? 's' : ''})</span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-slate-500" aria-hidden />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-500" aria-hidden />
        )}
      </button>

      {expanded && (
        <div id="why-content" className="px-4 pb-4 space-y-3">
          {title && (
            <div className="text-xs font-bold uppercase tracking-wide text-slate-600 pt-1">
              {title}
            </div>
          )}

          <div className="space-y-2">
            {reasons.map((reason, i) => (
              <div
                key={i}
                className="bg-white rounded-md border border-slate-200 px-3 py-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-800">{reason.label}</span>
                  {reason.score !== undefined && (
                    <span className="text-xs font-mono font-bold text-orange-700 bg-orange-100 px-2 py-0.5 rounded-full">
                      +{reason.score.toFixed(1)}
                    </span>
                  )}
                </div>
                {reason.evidence && (
                  <p className="text-xs text-slate-600 mt-1">{reason.evidence}</p>
                )}
                {reason.threshold && (
                  <p className="text-xs text-slate-400 mt-0.5">
                    Threshold: {reason.threshold}
                  </p>
                )}
              </div>
            ))}
          </div>

          {methodology && (
            <div className="text-xs text-slate-500 border-t border-slate-200 pt-2">
              <span className="font-semibold">Method:</span> {methodology}
            </div>
          )}

          {disclaimer && (
            <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 mt-0.5 flex-shrink-0" aria-hidden />
              <p className="text-xs text-amber-800">{disclaimer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
