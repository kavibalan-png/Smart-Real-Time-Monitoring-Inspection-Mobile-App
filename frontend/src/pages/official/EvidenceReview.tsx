/**
 * Evidence Review + Digital Thread page.
 * Shows inspection timeline, evidence integrity, official decision.
 */
import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, ShieldCheck, ShieldAlert, MapPin, Clock,
  CheckCircle2, XCircle, AlertCircle, ChevronRight,
  FileCheck, RefreshCw
} from 'lucide-react'
import { inspectionsApi, evidenceApi } from '../../services/api'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { EvidenceIntegrityBadge } from '../../components/shared/EvidenceIntegrityBadge'
import { PageLoader } from '../../components/shared/LoadingSpinner'
import { format } from 'date-fns'

export function EvidenceReview() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const inspectionId = parseInt(id || '0')
  const [verificationResults, setVerificationResults] = useState<Record<number, any>>({})
  const [verifying, setVerifying] = useState<number | null>(null)

  const { data: inspection, isLoading } = useQuery({
    queryKey: ['inspection', inspectionId],
    queryFn: () => inspectionsApi.get(inspectionId).then((r) => r.data),
  })

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline', inspectionId],
    queryFn: () => inspectionsApi.timeline(inspectionId).then((r) => r.data),
  })

  const decisionMutation = useMutation({
    mutationFn: (data: any) => inspectionsApi.decision(inspectionId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inspection', inspectionId] })
      navigate(-1)
    },
  })

  const handleVerify = async (evidenceId: number) => {
    setVerifying(evidenceId)
    try {
      const resp = await evidenceApi.verify(evidenceId)
      setVerificationResults((prev) => ({ ...prev, [evidenceId]: resp.data }))
    } finally {
      setVerifying(null)
    }
  }

  if (isLoading || !inspection) return <PageLoader label="Loading inspection review..." />

  const TIMELINE_COLORS: Record<string, string> = {
    ANOMALY: 'bg-orange-500',
    ASSIGNMENT: 'bg-brand-600',
    INSPECTION_START: 'bg-indigo-500',
    EVIDENCE_CAPTURE: 'bg-teal-500',
    EVIDENCE_HASH: 'bg-teal-600',
    INSPECTION_SUBMITTED: 'bg-purple-500',
    OFFICIAL_REVIEW: 'bg-slate-600',
    DECISION: 'bg-emerald-600',
    FOLLOWUP: 'bg-blue-500',
  }

  return (
    <div className="p-5 max-w-screen-xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-secondary py-1.5">
          <ArrowLeft className="w-4 h-4" aria-hidden />
          Back
        </button>
        <div>
          <h1 className="text-lg font-bold text-slate-900">Inspection Review</h1>
          <div className="text-sm text-slate-500">{inspection.inspection_code} — {inspection.project_name}</div>
        </div>
        <StatusBadge status={inspection.status} className="ml-auto" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Evidence + Integrity */}
        <div className="space-y-4">
          <div className="card">
            <div className="card-header font-semibold text-slate-800">Evidence & Integrity Verification</div>
            <div className="p-4 space-y-3">
              <div className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded px-3 py-2">
                Evidence Integrity Verification uses SHA-256 hashing to confirm files have not been
                modified since upload. This verifies byte consistency, not scene authenticity.
              </div>

              {(!inspection.evidence || inspection.evidence.length === 0) ? (
                <div className="text-sm text-slate-400 text-center py-4">No evidence uploaded</div>
              ) : (
                inspection.evidence.map((ev: any) => {
                  const vr = verificationResults[ev.id]
                  return (
                    <div key={ev.id} className="border border-slate-200 rounded-md p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-medium text-slate-800">{ev.evidence_code}</div>
                          <div className="text-xs text-slate-500">
                            {ev.evidence_type} — {format(new Date(ev.captured_at), 'dd MMM, HH:mm')}
                            {ev.captured_offline && (
                              <span className="ml-1 text-amber-600 font-medium">[OFFLINE]</span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => handleVerify(ev.id)}
                          disabled={verifying === ev.id}
                          className="btn-secondary text-xs py-1"
                          aria-label={`Verify integrity of ${ev.evidence_code}`}
                        >
                          <RefreshCw className={`w-3 h-3 ${verifying === ev.id ? 'animate-spin' : ''}`} aria-hidden />
                          Verify
                        </button>
                      </div>

                      {/* GPS */}
                      {ev.latitude && (
                        <div className="flex items-center gap-1.5 text-xs text-slate-600">
                          <MapPin className="w-3 h-3" aria-hidden />
                          <span className="font-mono">
                            {ev.latitude.toFixed(6)}, {ev.longitude.toFixed(6)}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded-full font-semibold ${
                            ev.gps_confidence === 'HIGH' ? 'bg-emerald-100 text-emerald-700' :
                            ev.gps_confidence === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {ev.gps_confidence}
                          </span>
                        </div>
                      )}

                      {/* Hash */}
                      {ev.sha256_hash && (
                        <div className="text-xs font-mono text-slate-500 break-all">
                          SHA-256: {ev.sha256_hash}
                        </div>
                      )}

                      {/* Verification result */}
                      {vr && (
                        <EvidenceIntegrityBadge result={vr.result} hash={vr.computed_hash} showHash />
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </div>

          {/* Checklist summary */}
          {inspection.checklist && inspection.checklist.length > 0 && (
            <div className="card">
              <div className="card-header font-semibold text-slate-800">Checklist Results</div>
              <div className="divide-y divide-slate-100">
                {inspection.checklist.map((item: any) => (
                  <div key={item.item_key} className="px-4 py-2.5 flex items-center gap-3">
                    <ValueIcon value={item.value} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-slate-800 truncate">{item.item_label}</div>
                      {item.observation && (
                        <div className="text-xs text-slate-500 truncate">{item.observation}</div>
                      )}
                    </div>
                    {item.is_critical && (
                      <span className="text-xs text-red-500 font-bold flex-shrink-0">CRITICAL</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Timeline + Decision */}
        <div className="space-y-4">
          {/* Digital Thread */}
          <div className="card">
            <div className="card-header font-semibold text-slate-800">Evidence Digital Thread</div>
            <div className="p-4">
              {timelineLoading ? (
                <div className="text-sm text-slate-400">Loading timeline...</div>
              ) : (
                <div className="relative">
                  {(timeline || []).map((event: any, i: number) => (
                    <div key={i} className="timeline-item">
                      <div className="timeline-line" aria-hidden />
                      <div
                        className={`timeline-dot ${TIMELINE_COLORS[event.event_type] || 'bg-slate-400'}`}
                        aria-hidden
                      />
                      <div>
                        <div className="text-xs font-semibold text-slate-700">{event.description}</div>
                        <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                          <Clock className="w-3 h-3" aria-hidden />
                          {format(new Date(event.timestamp), 'dd MMM, HH:mm:ss')}
                          {event.actor && <span>— {event.actor}</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Official Decision */}
          {['SUBMITTED', 'UNDER_REVIEW'].includes(inspection.status) && (
            <div className="card border-brand-200">
              <div className="card-header">
                <div className="font-semibold text-slate-800">Official Decision</div>
                <div className="text-xs text-slate-500 mt-0.5">
                  AI assists. Authorized official decides.
                </div>
              </div>
              <div className="p-4 space-y-3">
                <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2 font-medium">
                  SYSTEM RECOMMENDATION: Human verification required before decision
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { value: 'APPROVED', label: 'Approve', color: 'bg-emerald-600 hover:bg-emerald-700', icon: <CheckCircle2 className="w-4 h-4" /> },
                    { value: 'REINSPECTION', label: 'Request Reinspection', color: 'bg-orange-600 hover:bg-orange-700', icon: <RefreshCw className="w-4 h-4" /> },
                    { value: 'ESCALATED', label: 'Escalate', color: 'bg-red-600 hover:bg-red-700', icon: <AlertCircle className="w-4 h-4" /> },
                    { value: 'CLOSED', label: 'Close', color: 'bg-slate-600 hover:bg-slate-700', icon: <XCircle className="w-4 h-4" /> },
                  ].map((action) => (
                    <button
                      key={action.value}
                      onClick={() => decisionMutation.mutate({ decision: action.value, decision_notes: `Official decision: ${action.value}` })}
                      disabled={decisionMutation.isPending}
                      className={`flex items-center justify-center gap-2 py-2.5 rounded-md text-white text-sm font-medium transition-colors ${action.color}`}
                      aria-label={action.label}
                    >
                      {action.icon}
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Existing decision */}
          {inspection.official_decision && (
            <div className="card p-4 bg-slate-50">
              <div className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-1">Decision Made</div>
              <StatusBadge status={inspection.official_decision} />
              {inspection.decision_notes && (
                <p className="text-sm text-slate-700 mt-2">{inspection.decision_notes}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ValueIcon({ value }: { value: string | null }) {
  if (value === 'PASS') return <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" aria-label="Pass" />
  if (value === 'FAIL') return <XCircle className="w-4 h-4 text-red-600 flex-shrink-0" aria-label="Fail" />
  if (value === 'PARTIAL') return <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" aria-label="Partial" />
  return <span className="w-4 h-4 text-slate-400 flex-shrink-0 text-xs font-bold" aria-label="Not observed">—</span>
}
