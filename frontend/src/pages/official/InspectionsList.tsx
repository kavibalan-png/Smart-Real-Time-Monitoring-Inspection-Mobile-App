import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, Eye, Calendar } from 'lucide-react'
import { inspectionsApi } from '../../services/api'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { PageLoader } from '../../components/shared/LoadingSpinner'
import { format } from 'date-fns'

export function InspectionsList() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['inspections-all'],
    queryFn: () => inspectionsApi.list({ per_page: 50 }).then((r) => r.data),
  })

  if (isLoading) return <PageLoader label="Loading inspections..." />

  return (
    <div className="p-5 max-w-screen-xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">Inspections</h1>
        <div className="text-sm text-slate-500">{data?.total || 0} total</div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm" role="table" aria-label="Inspections list">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Code</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Project</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Rating</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(data?.items || []).map((insp: any) => (
              <tr key={insp.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{insp.inspection_code}</td>
                <td className="px-4 py-3 font-medium text-slate-900 max-w-xs truncate">{insp.project_name}</td>
                <td className="px-4 py-3"><StatusBadge status={insp.status} size="sm" /></td>
                <td className="px-4 py-3">
                  {insp.overall_rating ? <StatusBadge status={insp.overall_rating} size="sm" /> : <span className="text-slate-400">—</span>}
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">
                  {insp.start_time ? format(new Date(insp.start_time), 'dd MMM yyyy') : format(new Date(insp.created_at), 'dd MMM yyyy')}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => navigate(`/inspections/${insp.id}/review`)}
                    className="btn-secondary text-xs py-1 px-2"
                    aria-label={`View ${insp.inspection_code}`}
                  >
                    <Eye className="w-3.5 h-3.5" aria-hidden />
                    Review
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
