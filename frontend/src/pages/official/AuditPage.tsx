import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Shield, Lock } from 'lucide-react'
import { auditApi } from '../../services/api'
import { PageLoader } from '../../components/shared/LoadingSpinner'
import { format } from 'date-fns'

const ACTION_COLORS: Record<string, string> = {
  LOGIN: 'bg-blue-100 text-blue-700',
  LOGOUT: 'bg-slate-100 text-slate-600',
  ASSIGNMENT: 'bg-orange-100 text-orange-700',
  INSPECTION_START: 'bg-indigo-100 text-indigo-700',
  EVIDENCE_CAPTURE: 'bg-teal-100 text-teal-700',
  EVIDENCE_HASH: 'bg-teal-100 text-teal-700',
  EVIDENCE_VERIFY: 'bg-emerald-100 text-emerald-700',
  DECISION: 'bg-purple-100 text-purple-700',
  FOLLOWUP: 'bg-brand-100 text-brand-700',
  ANOMALY: 'bg-amber-100 text-amber-700',
}

export function AuditPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['audit', page],
    queryFn: () => auditApi.list({ page, per_page: 50 }).then((r) => r.data),
  })

  if (isLoading) return <PageLoader label="Loading audit trail..." />

  return (
    <div className="p-5 max-w-screen-xl mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <Shield className="w-5 h-5 text-brand-700" aria-hidden />
        <h1 className="text-xl font-bold text-slate-900">Audit Trail</h1>
        <span className="badge bg-slate-100 text-slate-600 ml-auto">{data?.total || 0} events</span>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-3 py-2">
        <Lock className="w-3.5 h-3.5 flex-shrink-0" aria-hidden />
        Audit logs are append-only and read-only. Modification is not permitted.
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm" role="table" aria-label="Audit log entries">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase w-44">Timestamp</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Action</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">User</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Role</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Resource</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono text-xs">
            {(data?.items || []).map((log: any) => (
              <tr key={log.id} className="hover:bg-slate-50">
                <td className="px-4 py-2.5 text-slate-500">
                  {format(new Date(log.timestamp), 'dd MMM HH:mm:ss')}
                </td>
                <td className="px-4 py-2.5">
                  <span className={`badge text-xs ${ACTION_COLORS[log.action] || 'bg-slate-100 text-slate-600'}`}>
                    {log.action}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-slate-700">{log.user_id || '—'}</td>
                <td className="px-4 py-2.5 text-slate-500">{log.role || '—'}</td>
                <td className="px-4 py-2.5 text-slate-600">
                  {log.resource_type ? `${log.resource_type}/${log.resource_id}` : '—'}
                </td>
                <td className="px-4 py-2.5">
                  <span className={`text-xs font-semibold ${
                    log.result === 'SUCCESS' ? 'text-emerald-600' :
                    log.result === 'FAILURE' ? 'text-red-600' : 'text-amber-600'
                  }`}>
                    {log.result}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-50">Previous</button>
          <span className="text-sm text-slate-600">Page {page} of {data.pages}</span>
          <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-50">Next</button>
        </div>
      )}
    </div>
  )
}
