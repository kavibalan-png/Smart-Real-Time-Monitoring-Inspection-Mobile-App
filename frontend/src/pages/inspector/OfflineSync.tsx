/**
 * Offline sync page — shows pending operations and sync progress.
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, CheckCircle2, XCircle, WifiOff, Wifi, ArrowLeft } from 'lucide-react'
import { getPendingOperations, getPendingCount } from '../../offline/offlineDB'
import { syncPendingOperations } from '../../offline/syncService'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import type { OfflineOperation } from '../../types'

export function OfflineSync() {
  const navigate = useNavigate()
  const isOnline = useOnlineStatus()
  const [pending, setPending] = useState<OfflineOperation[]>([])
  const [syncing, setSyncing] = useState(false)
  const [result, setResult] = useState<{ success: number; failed: number } | null>(null)
  const [progress, setProgress] = useState({ current: 0, total: 0, label: '' })

  useEffect(() => {
    getPendingOperations().then(setPending)
  }, [])

  const handleSync = async () => {
    if (!isOnline) return
    setSyncing(true)
    setResult(null)

    const syncResult = await syncPendingOperations((processed, total, label) => {
      setProgress({ current: processed, total, label })
    })

    setResult(syncResult)
    setSyncing(false)
    const updated = await getPendingOperations()
    setPending(updated)
  }

  const statusColors: Record<string, string> = {
    PENDING: 'bg-amber-100 text-amber-700',
    UPLOADING: 'bg-blue-100 text-blue-700',
    SUCCESS: 'bg-emerald-100 text-emerald-700',
    FAILED: 'bg-red-100 text-red-700',
    RETRY: 'bg-orange-100 text-orange-700',
  }

  return (
    <div className="p-4 max-w-md mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-secondary py-1.5" aria-label="Go back">
          <ArrowLeft className="w-4 h-4" aria-hidden />
        </button>
        <h1 className="font-bold text-slate-900">Sync Pending Data</h1>
      </div>

      {/* Network status */}
      <div className={`card p-3 flex items-center gap-2 ${
        isOnline ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'
      }`}>
        {isOnline ? (
          <>
            <Wifi className="w-5 h-5 text-emerald-600" aria-hidden />
            <span className="text-sm font-semibold text-emerald-800">Network connected — ready to sync</span>
          </>
        ) : (
          <>
            <WifiOff className="w-5 h-5 text-red-600" aria-hidden />
            <span className="text-sm font-semibold text-red-800">Offline — connect to sync</span>
          </>
        )}
      </div>

      {/* Summary */}
      <div className="card p-4 text-center">
        <div className="text-4xl font-bold text-slate-900">{pending.length}</div>
        <div className="text-sm text-slate-500 mt-1">Records Pending Synchronization</div>
      </div>

      {/* Progress */}
      {syncing && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <RefreshCw className="w-4 h-4 text-brand-600 animate-spin" aria-hidden />
            <span className="text-sm font-medium text-slate-700">Syncing...</span>
          </div>
          <div className="text-xs text-slate-500 mb-2">{progress.label}</div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full transition-all"
              style={{ width: progress.total > 0 ? `${(progress.current / progress.total) * 100}%` : '0%' }}
              role="progressbar"
              aria-valuenow={progress.current}
              aria-valuemax={progress.total}
            />
          </div>
          <div className="text-xs text-slate-500 mt-1">{progress.current} / {progress.total}</div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className={`card p-4 ${result.failed === 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'}`}>
          <div className="flex items-center gap-2">
            {result.failed === 0 ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" aria-hidden />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" aria-hidden />
            )}
            <div>
              <div className="text-sm font-semibold text-slate-800">
                {result.success} synced successfully{result.failed > 0 ? `, ${result.failed} failed` : ''}
              </div>
              {result.failed > 0 && (
                <div className="text-xs text-red-600 mt-0.5">Failed items will retry automatically</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Operations list */}
      {pending.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="font-semibold text-slate-800 text-sm">Pending Operations</span>
          </div>
          <div className="divide-y divide-slate-100">
            {pending.map((op) => (
              <div key={op.local_id} className="px-4 py-3 flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-800">{op.operation_type.replace(/_/g, ' ')}</div>
                  <div className="text-xs text-slate-500">
                    {new Date(op.created_at).toLocaleString('en-IN')}
                    {op.retry_count > 0 && ` · Retry ${op.retry_count}`}
                  </div>
                </div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${statusColors[op.sync_status] || ''}`}>
                  {op.sync_status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={handleSync}
        disabled={!isOnline || syncing || pending.length === 0}
        className="btn-primary w-full justify-center py-3"
        aria-label="Sync all pending data"
      >
        <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} aria-hidden />
        {syncing ? 'Syncing...' : `Sync ${pending.length} Record${pending.length !== 1 ? 's' : ''}`}
      </button>

      <div className="text-xs text-slate-500 text-center">
        Data is safely stored locally. No information will be lost if sync fails.
      </div>
    </div>
  )
}
