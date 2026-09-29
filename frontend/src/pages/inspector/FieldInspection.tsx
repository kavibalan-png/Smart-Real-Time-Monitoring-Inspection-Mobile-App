/**
 * Field Inspection page — mobile-first, offline-capable.
 * GPS capture, photo upload, checklist, sync.
 */
import React, { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  MapPin, Camera, CheckCircle2, XCircle, AlertCircle, Minus,
  Upload, WifiOff, Navigation, Clock, Send, ChevronDown, ChevronUp
} from 'lucide-react'
import { inspectionsApi, evidenceApi } from '../../services/api'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { PageLoader } from '../../components/shared/LoadingSpinner'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import { queueOperation, queueEvidenceFile } from '../../offline/offlineDB'
import { format } from 'date-fns'
import type { ChecklistValue } from '../../types'

const CHECKLIST_VALUES: { value: ChecklistValue; label: string; icon: React.ReactNode; color: string }[] = [
  { value: 'PASS', label: 'Pass', icon: <CheckCircle2 className="w-4 h-4" />, color: 'text-emerald-600 border-emerald-300 bg-emerald-50' },
  { value: 'FAIL', label: 'Fail', icon: <XCircle className="w-4 h-4" />, color: 'text-red-600 border-red-300 bg-red-50' },
  { value: 'PARTIAL', label: 'Partial', icon: <AlertCircle className="w-4 h-4" />, color: 'text-amber-600 border-amber-300 bg-amber-50' },
  { value: 'NOT_OBSERVED', label: 'N/A', icon: <Minus className="w-4 h-4" />, color: 'text-slate-500 border-slate-300 bg-slate-50' },
]

export function FieldInspection() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const isOnline = useOnlineStatus()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const inspectionId = parseInt(id || '0')

  const [gpsData, setGpsData] = useState<GeolocationPosition | null>(null)
  const [gpsError, setGpsError] = useState<string | null>(null)
  const [checklistValues, setChecklistValues] = useState<Record<string, ChecklistValue>>({})
  const [observations, setObservations] = useState<Record<string, string>>({})
  const [rating, setRating] = useState('NEEDS_IMPROVEMENT')
  const [summaryNotes, setSummaryNotes] = useState('')
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())
  const [uploadedEvidence, setUploadedEvidence] = useState<any[]>([])
  const [started, setStarted] = useState(false)

  const { data: inspection, isLoading } = useQuery({
    queryKey: ['inspection', inspectionId],
    queryFn: () => inspectionsApi.get(inspectionId).then((r) => r.data),
  })

  const startMutation = useMutation({
    mutationFn: (gps: any) => inspectionsApi.start(inspectionId, gps),
    onSuccess: () => {
      setStarted(true)
      qc.invalidateQueries({ queryKey: ['inspection', inspectionId] })
    },
  })

  const submitMutation = useMutation({
    mutationFn: (data: any) => inspectionsApi.submit(inspectionId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-inspections'] })
      navigate('/inspector/home')
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!isOnline) {
        // Queue offline
        await queueEvidenceFile(inspectionId, file, {
          filename: file.name,
          latitude: gpsData?.coords.latitude,
          longitude: gpsData?.coords.longitude,
          gps_accuracy: gpsData?.coords.accuracy,
          evidence_type: 'PHOTO',
        })
        return { offline: true, local_id: `offline_${Date.now()}` }
      }

      const formData = new FormData()
      formData.append('file', file)
      formData.append('inspection_id', String(inspectionId))
      if (gpsData) {
        formData.append('latitude', String(gpsData.coords.latitude))
        formData.append('longitude', String(gpsData.coords.longitude))
        formData.append('gps_accuracy', String(gpsData.coords.accuracy))
      }
      formData.append('captured_offline', String(!isOnline))
      formData.append('evidence_type', 'PHOTO')
      const resp = await evidenceApi.upload(formData)
      return resp.data
    },
    onSuccess: (data) => {
      setUploadedEvidence((prev) => [...prev, data])
      qc.invalidateQueries({ queryKey: ['inspection', inspectionId] })
    },
  })

  const captureGPS = () => {
    setGpsError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => setGpsData(pos),
      (err) => setGpsError(`GPS unavailable: ${err.message}`),
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  const handleStart = () => {
    const gps = {
      latitude: gpsData?.coords.latitude || 19.0448,
      longitude: gpsData?.coords.longitude || 72.8558,
      gps_accuracy: gpsData?.coords.accuracy || 15,
      offline: !isOnline,
    }
    if (isOnline) {
      startMutation.mutate(gps)
    } else {
      // Queue start operation offline
      queueOperation('INSPECTION_START', { inspection_id: inspectionId, ...gps })
      setStarted(true)
    }
  }

  const handleSubmit = async () => {
    const checklist_items = (inspection?.checklist || []).map((item: any) => ({
      item_key: item.item_key,
      value: checklistValues[item.item_key] || 'NOT_OBSERVED',
      observation: observations[item.item_key] || null,
      captured_offline: !isOnline,
    }))

    if (isOnline) {
      submitMutation.mutate({ overall_rating: rating, summary_notes: summaryNotes, checklist_items })
    } else {
      await queueOperation('INSPECTION_SUBMIT', {
        inspection_id: inspectionId,
        overall_rating: rating,
        summary_notes: summaryNotes,
        checklist_items,
      })
      navigate('/inspector/sync')
    }
  }

  if (isLoading || !inspection) return <PageLoader label="Loading inspection..." />

  const isActive = started || inspection.status === 'IN_PROGRESS'

  return (
    <div className="p-4 max-w-md mx-auto space-y-4 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-bold text-slate-900">{inspection.project_name}</h1>
          <div className="text-xs text-slate-500">{inspection.inspection_code}</div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={inspection.status} size="sm" />
          {!isOnline && (
            <div className="flex items-center gap-1 text-xs text-red-600 font-semibold">
              <WifiOff className="w-3 h-3" aria-hidden />
              OFFLINE
            </div>
          )}
        </div>
      </div>

      {/* GPS capture */}
      <div className="card p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Navigation className="w-4 h-4 text-brand-600" aria-hidden />
            GPS Location
          </div>
          <button onClick={captureGPS} className="btn-secondary text-xs py-1">
            Capture GPS
          </button>
        </div>
        {gpsData ? (
          <div className="text-sm space-y-1">
            <div className="font-mono text-slate-700">
              {gpsData.coords.latitude.toFixed(6)}, {gpsData.coords.longitude.toFixed(6)}
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                gpsData.coords.accuracy < 5
                  ? 'bg-emerald-100 text-emerald-700'
                  : gpsData.coords.accuracy < 20
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-red-100 text-red-700'
              }`}>
                {gpsData.coords.accuracy < 5 ? 'HIGH' : gpsData.coords.accuracy < 20 ? 'MEDIUM' : 'LOW'} CONFIDENCE
              </span>
              <span className="text-xs text-slate-500">±{gpsData.coords.accuracy.toFixed(0)}m</span>
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3" aria-hidden />
                {format(new Date(), 'HH:mm:ss')}
              </span>
            </div>
          </div>
        ) : (
          <div className="text-sm text-slate-500">
            {gpsError || 'GPS not captured. Tap "Capture GPS" to record location.'}
          </div>
        )}
        {gpsData && gpsData.coords.accuracy >= 20 && (
          <div className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
            Low GPS confidence — manual verification recommended
          </div>
        )}
      </div>

      {/* Start inspection */}
      {!isActive && (
        <button
          onClick={handleStart}
          disabled={startMutation.isPending}
          className="btn-primary w-full justify-center py-3 text-base"
        >
          <Play className="w-5 h-5" aria-hidden />
          {startMutation.isPending ? 'Starting...' : 'Start Inspection'}
        </button>
      )}

      {/* Checklist */}
      {isActive && (
        <>
          <div className="card">
            <div className="card-header">
              <span className="font-semibold text-slate-800">Inspection Checklist</span>
            </div>
            <div className="divide-y divide-slate-100">
              {(inspection.checklist || []).map((item: any) => (
                <ChecklistItemRow
                  key={item.item_key}
                  item={item}
                  value={checklistValues[item.item_key] || null}
                  observation={observations[item.item_key] || ''}
                  expanded={expandedItems.has(item.item_key)}
                  onToggleExpand={() => {
                    const next = new Set(expandedItems)
                    if (next.has(item.item_key)) next.delete(item.item_key)
                    else next.add(item.item_key)
                    setExpandedItems(next)
                  }}
                  onValueChange={(v) => setChecklistValues((prev) => ({ ...prev, [item.item_key]: v }))}
                  onObservationChange={(obs) => setObservations((prev) => ({ ...prev, [item.item_key]: obs }))}
                />
              ))}
            </div>
          </div>

          {/* Evidence */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 font-semibold text-slate-700">
                <Camera className="w-4 h-4" aria-hidden />
                Evidence ({uploadedEvidence.length + (inspection.evidence?.length || 0)})
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadMutation.isPending}
                className="btn-primary text-xs py-1.5"
              >
                <Upload className="w-3.5 h-3.5" aria-hidden />
                {uploadMutation.isPending ? 'Uploading...' : 'Add Photo'}
              </button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              aria-label="Upload evidence photo"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) uploadMutation.mutate(file)
                e.target.value = ''
              }}
            />
            {uploadedEvidence.map((ev, i) => (
              <div key={i} className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-2 py-1.5 mb-1.5">
                {ev.offline ? (
                  <span>📁 Evidence queued offline (local_id: {ev.local_id?.slice(0, 12)}...)</span>
                ) : (
                  <>
                    <span>✓ Evidence captured — {ev.evidence_code}</span>
                    {ev.sha256_hash && (
                      <div className="font-mono text-slate-500 mt-0.5">
                        SHA-256: {ev.sha256_hash.slice(0, 20)}...
                      </div>
                    )}
                    <div className="mt-0.5">GPS: {ev.gps_confidence || 'UNKNOWN'}</div>
                  </>
                )}
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="card p-4 space-y-3">
            <div className="font-semibold text-slate-700">Overall Assessment</div>
            <div>
              <label htmlFor="rating" className="block text-sm text-slate-600 mb-1">Overall Rating</label>
              <select
                id="rating"
                value={rating}
                onChange={(e) => setRating(e.target.value)}
                className="w-full rounded-md border border-slate-300 text-sm py-2 px-3"
                aria-required="true"
              >
                <option value="SATISFACTORY">Satisfactory</option>
                <option value="NEEDS_IMPROVEMENT">Needs Improvement</option>
                <option value="UNSATISFACTORY">Unsatisfactory</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
            <div>
              <label htmlFor="summary" className="block text-sm text-slate-600 mb-1">Summary Notes</label>
              <textarea
                id="summary"
                value={summaryNotes}
                onChange={(e) => setSummaryNotes(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-slate-300 text-sm py-2 px-3 resize-none"
                placeholder="Describe key observations from this inspection..."
                aria-required="true"
              />
            </div>

            {!isOnline && (
              <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                <WifiOff className="w-3.5 h-3.5 flex-shrink-0" aria-hidden />
                Offline — data will be saved locally and synced when connected
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={submitMutation.isPending || !summaryNotes}
              className="btn-primary w-full justify-center py-2.5"
            >
              <Send className="w-4 h-4" aria-hidden />
              {isOnline
                ? (submitMutation.isPending ? 'Submitting...' : 'Submit Inspection')
                : 'Save Offline & Queue Sync'
              }
            </button>
          </div>
        </>
      )}
    </div>
  )
}

function ChecklistItemRow({
  item, value, observation, expanded,
  onToggleExpand, onValueChange, onObservationChange,
}: {
  item: any
  value: ChecklistValue | null
  observation: string
  expanded: boolean
  onToggleExpand: () => void
  onValueChange: (v: ChecklistValue) => void
  onObservationChange: (obs: string) => void
}) {
  return (
    <div className="p-3">
      <button
        onClick={onToggleExpand}
        className="w-full flex items-center gap-2 text-left"
        aria-expanded={expanded}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-medium text-slate-800 truncate">{item.item_label}</span>
            {item.is_critical && (
              <span className="text-xs text-red-600 font-bold">*</span>
            )}
          </div>
          <div className="text-xs text-slate-500">{item.category}</div>
        </div>
        <div className="flex items-center gap-2">
          {value && (
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
              CHECKLIST_VALUES.find((v) => v.value === value)?.color || ''
            }`}>
              {value}
            </span>
          )}
          {expanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {expanded && (
        <div className="mt-3 space-y-2 pl-2" id={`checklist-${item.item_key}`}>
          <div className="grid grid-cols-4 gap-1.5" role="group" aria-label={`Rating for ${item.item_label}`}>
            {CHECKLIST_VALUES.map((opt) => (
              <button
                key={opt.value}
                onClick={() => onValueChange(opt.value)}
                className={`flex flex-col items-center gap-0.5 py-2 rounded-md border text-xs font-medium transition-colors ${
                  value === opt.value ? opt.color : 'border-slate-200 text-slate-500 hover:bg-slate-50'
                }`}
                aria-pressed={value === opt.value}
              >
                {opt.icon}
                {opt.label}
              </button>
            ))}
          </div>
          <textarea
            value={observation}
            onChange={(e) => onObservationChange(e.target.value)}
            rows={2}
            className="w-full rounded border border-slate-200 text-xs py-1.5 px-2 resize-none"
            placeholder="Add observation..."
            aria-label={`Observation for ${item.item_label}`}
          />
        </div>
      )}
    </div>
  )
}
