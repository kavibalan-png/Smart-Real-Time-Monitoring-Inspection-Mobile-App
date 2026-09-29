import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileCheck, Calendar, CheckCircle2 } from 'lucide-react'
import { followupApi } from '../../services/api'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { PageLoader } from '../../components/shared/LoadingSpinner'
import { format } from 'date-fns'

export function FollowupPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['followups'],
    queryFn: () => followupApi.list({ per_page: 50 }).then((r) => r.data),
  })

  if (isLoading) return <PageLoader label="Loading follow-ups..." />

  return (
    <div className="p-5 max-w-screen-xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">Follow-up & Compliance</h1>
        <div className="text-sm text-slate-500">{data?.total || 0} items</div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Code</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Action</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Description</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Due Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(data?.items || []).map((fu: any) => (
              <tr key={fu.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{fu.followup_code}</td>
                <td className="px-4 py-3">
                  <span className="font-medium text-slate-800">{fu.action_type.replace(/_/g, ' ')}</span>
                </td>
                <td className="px-4 py-3 text-slate-600 max-w-xs truncate">{fu.description}</td>
                <td className="px-4 py-3 text-xs text-slate-500 flex items-center gap-1">
                  <Calendar className="w-3 h-3" aria-hidden />
                  {fu.due_date ? format(new Date(fu.due_date), 'dd MMM yyyy') : '—'}
                </td>
                <td className="px-4 py-3"><StatusBadge status={fu.status} size="sm" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
