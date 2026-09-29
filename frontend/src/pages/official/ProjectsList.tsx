import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MapPin, Eye, Search, AlertTriangle } from 'lucide-react'
import { projectsApi } from '../../services/api'
import { HealthIndexRing } from '../../components/shared/HealthIndexRing'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { PageLoader } from '../../components/shared/LoadingSpinner'

export function ProjectsList() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['projects', search, riskFilter, page],
    queryFn: () =>
      projectsApi.list({ search: search || undefined, risk_level: riskFilter || undefined, page, per_page: 20 })
        .then((r) => r.data),
  })

  if (isLoading && !data) return <PageLoader label="Loading projects..." />

  return (
    <div className="p-5 max-w-screen-xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">Projects</h1>
        <div className="text-sm text-slate-500">{data?.total || 0} projects</div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-52">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" aria-hidden />
          <input
            type="search"
            placeholder="Search projects..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            aria-label="Search projects"
          />
        </div>
        <select
          value={riskFilter}
          onChange={(e) => { setRiskFilter(e.target.value); setPage(1) }}
          className="border border-slate-300 rounded-md text-sm px-3 py-2 focus:ring-2 focus:ring-brand-500 outline-none"
          aria-label="Filter by risk level"
        >
          <option value="">All Risk Levels</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      {/* Project grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {(data?.items || []).map((project: any) => (
          <div
            key={project.id}
            className={`card cursor-pointer hover:shadow-md transition-shadow overflow-hidden ${
              project.is_hero_project ? 'ring-2 ring-orange-400' : ''
            }`}
            onClick={() => navigate(`/projects/${project.id}`)}
            role="article"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && navigate(`/projects/${project.id}`)}
            aria-label={`${project.project_name} — health ${project.health_index}/100`}
          >
            <div className={`h-1 ${
              project.risk_level === 'CRITICAL' ? 'bg-red-500' :
              project.risk_level === 'HIGH' ? 'bg-orange-500' :
              project.risk_level === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500'
            }`} aria-hidden />
            <div className="p-4 space-y-3">
              <div className="flex items-start gap-3">
                <HealthIndexRing score={project.health_index} size="sm" showLabel={false} />
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-slate-900 text-sm leading-tight line-clamp-2">
                    {project.project_name}
                  </div>
                  <div className="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
                    <MapPin className="w-3 h-3" aria-hidden />
                    {project.district}
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-1">
                <StatusBadge status={project.status} size="sm" />
                {project.open_findings > 0 && (
                  <span className="badge bg-red-100 text-red-700">
                    {project.open_findings} findings
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    project.cctv_status === 'LIVE' ? 'bg-emerald-500' :
                    project.cctv_status === 'OFFLINE' ? 'bg-red-500' : 'bg-amber-500'
                  }`} aria-hidden />
                  CCTV: {project.cctv_status}
                </span>
                {project.is_hero_project && (
                  <span className="text-teal-600 font-semibold">HERO</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="btn-secondary py-1.5 px-3 text-xs disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-slate-600">
            Page {page} of {data.pages}
          </span>
          <button
            disabled={page >= data.pages}
            onClick={() => setPage(page + 1)}
            className="btn-secondary py-1.5 px-3 text-xs disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
