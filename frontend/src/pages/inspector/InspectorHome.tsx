/**
 * Inspector Mobile Home — mobile-first PWA view.
 * Shows today's assignments with offline capability.
 */
import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ClipboardList, MapPin, AlertTriangle, Play,
  WifiOff, Wifi, RefreshCw, Clock, ChevronRight
} from 'lucide-react'
import { inspectionsApi } from '../../services/api'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import { getPendingCount } from '../../offline/offlineDB'
import { format } from 'date-fns'

export function InspectorHome() {
  const navigate = useNavigate()
  const isOnline = useOnlineStatus()
  const [pendingCount, setPendingCount] = useState(0)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['my-inspections'],
    queryFn: () => inspectionsApi.list({ per_page: 20 }).then((r) => r.data),
    enabled: isOnline,
  })

  useEffect(() => {
    getPendingCount().then(setPendingCount)
  }, [])

  const activeInspections = (data?.items || []).filter((i: any) =>
    ['ASSIGNED', 'IN_PROGRESS', 'NOTIFIED'].includes(i.status)
  )
  const completedInspections = (data?.items || []).filter((i: any) =>
    ['SUBMITTED', 'APPROVED', 'UNDER_REVIEW'].includes(i.status)
  )

  return (
    <div className="p-4 max-w-md mx-auto space-y-4">
      {/* Status bar */}
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">My Inspections</h1>
        <div className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${
          isOnline ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
        }`}>
          {isOnline ? <Wifi className="w-3 h-3" aria-hidden /> : <WifiOff className="w-3 h-3" aria-hidden />}
          {isOnline ? 'Online' : 'Offline Mode'}
        </div>
      </div>

      {/* Offline banner */}
      {!isOnline && (
        <div className="card p-3 bg-amber-50 border-amber-200">
          <div className="flex items-center gap-2">
            <WifiOff className="w-4 h-4 text-amber-600" aria-hidden />
            <div>
              <div className="text-sm font-semibold text-amber-800">Offline Mode Active</div>
              <div className="text-xs text-amber-700">All data saved locally. Sync when online.</div>
            </div>
          </div>
        </div>
      )}

      {/* Pending sync */}
      {pendingCount > 0 && (
        <div
          className="card p-3 bg-blue-50 border-blue-200 flex items-center justify-between cursor-pointer hover:bg-blue-100"
          onClick={() => navigate('/inspector/sync')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/inspector/sync')}
          aria-label={`${pendingCount} records pending sync`}
        >
          <div className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-blue-600" aria-hidden />
            <span className="text-sm font-semibold text-blue-800">
              {pendingCount} record{pendingCount !== 1 ? 's' : ''} pending sync
            </span>
          </div>
          <span className="text-xs text-blue-600 font-medium">Sync Now →</span>
        </div>
      )}

      {/* Active assignments */}
      <section aria-label="Active assignments">
        <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-2">
          Active Assignments ({activeInspections.length})
        </h2>
        {isLoading && isOnline ? (
          <div className="card p-5 text-center text-sm text-slate-400">Loading...</div>
        ) : activeInspections.length === 0 ? (
          <div className="card p-5 text-center">
            <ClipboardList className="w-8 h-8 text-slate-300 mx-auto mb-2" aria-hidden />
            <p className="text-sm text-slate-400">No active assignments</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeInspections.map((insp: any) => (
              <InspectionCard
                key={insp.id}
                inspection={insp}
                onStart={() => navigate(`/inspector/inspection/${insp.id}`)}
              />
            ))}
          </div>
        )}
      </section>

      {/* Recent completed */}
      {completedInspections.length > 0 && (
        <section aria-label="Completed inspections">
          <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-2">
            Recent Completed
          </h2>
          <div className="space-y-2">
            {completedInspections.slice(0, 3).map((insp: any) => (
              <div
                key={insp.id}
                className="card p-3 flex items-center gap-3 cursor-pointer hover:bg-slate-50"
                onClick={() => navigate(`/inspector/inspection/${insp.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && navigate(`/inspector/inspection/${insp.id}`)}
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-800 truncate">{insp.project_name}</div>
                  <div className="text-xs text-slate-500">
                    {insp.start_time ? format(new Date(insp.start_time), 'dd MMM, HH:mm') : 'Not started'}
                  </div>
                </div>
                <StatusBadge status={insp.status} size="sm" />
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

function InspectionCard({
  inspection,
  onStart,
}: {
  inspection: any
  onStart: () => void
}) {
  return (
    <div className="card overflow-hidden">
      <div className={`h-1 ${
        inspection.status === 'IN_PROGRESS' ? 'bg-indigo-500' : 'bg-orange-500'
      }`} aria-hidden />
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-slate-900 truncate">{inspection.project_name}</div>
            <div className="text-xs text-slate-500 mt-0.5">
              Code: {inspection.inspection_code}
            </div>
          </div>
          <StatusBadge status={inspection.status} size="sm" />
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
          <div className="flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-orange-500" aria-hidden />
            <span>SURPRISE</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" aria-hidden />
            <span>{format(new Date(inspection.created_at), 'dd MMM yyyy')}</span>
          </div>
        </div>

        <button
          onClick={onStart}
          className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium transition-colors ${
            inspection.status === 'IN_PROGRESS'
              ? 'bg-indigo-600 text-white hover:bg-indigo-700'
              : 'bg-orange-600 text-white hover:bg-orange-700'
          }`}
          aria-label={`${inspection.status === 'IN_PROGRESS' ? 'Continue' : 'Start'} inspection for ${inspection.project_name}`}
        >
          <Play className="w-4 h-4" aria-hidden />
          {inspection.status === 'IN_PROGRESS' ? 'Continue Inspection' : 'Start Inspection'}
        </button>
      </div>
    </div>
  )
}
