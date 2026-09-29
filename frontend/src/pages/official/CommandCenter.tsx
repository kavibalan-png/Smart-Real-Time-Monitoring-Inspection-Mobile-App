/**
 * Command Center — the most important screen.
 * Immediately answers: which project needs attention? why? what next?
 */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity, AlertTriangle, Building2, Search, Eye,
  TrendingUp, Camera, ClipboardCheck, ChevronRight,
  Zap, Clock
} from 'lucide-react'
import { monitoringApi, projectsApi, analyticsApi } from '../../services/api'
import { HealthIndexRing } from '../../components/shared/HealthIndexRing'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { WhyExplainer } from '../../components/shared/WhyExplainer'
import { DemoBanner } from '../../components/shared/DemoBanner'
import { PageLoader } from '../../components/shared/LoadingSpinner'
import { formatDistanceToNow } from 'date-fns'
import type { AnomalyEvent, MonitoringSummary, Project } from '../../types'
import clsx from 'clsx'

export function CommandCenter() {
  const navigate = useNavigate()

  const { data: summary, isLoading: summaryLoading } = useQuery<MonitoringSummary>({
    queryKey: ['monitoring-summary'],
    queryFn: () => monitoringApi.summary().then((r) => r.data),
    refetchInterval: 30000,
  })

  const { data: hero } = useQuery<Project>({
    queryKey: ['hero-project'],
    queryFn: () => projectsApi.hero().then((r) => r.data),
  })

  const { data: alerts } = useQuery<AnomalyEvent[]>({
    queryKey: ['alerts'],
    queryFn: () => monitoringApi.alerts({ limit: 5 }).then((r) => r.data),
    refetchInterval: 30000,
  })

  const { data: heroAnomaly } = useQuery({
    queryKey: ['hero-anomaly', hero?.id],
    queryFn: () => monitoringApi.anomalies(hero!.id).then((r) => r.data[0] || null),
    enabled: !!hero?.id,
  })

  const { data: dashboardData } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => analyticsApi.dashboard().then((r) => r.data),
  })

  if (summaryLoading) return <PageLoader label="Loading command center..." />

  const topAlerts = (alerts || []).slice(0, 5)

  return (
    <div className="p-5 space-y-5 max-w-screen-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Command Center</h1>
          <p className="text-sm text-slate-500">
            Real-time monitoring — {new Date().toLocaleString('en-IN', { dateStyle: 'full', timeStyle: 'short' })}
          </p>
        </div>
        <DemoBanner inline />
      </div>

      <DemoBanner />

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          label="Total Projects"
          value={summary?.total_projects || 0}
          icon={<Building2 className="w-4 h-4" />}
          color="blue"
        />
        <StatCard
          label="Attention Required"
          value={summary?.attention_required || 0}
          icon={<AlertTriangle className="w-4 h-4" />}
          color="orange"
          alert={!!summary?.attention_required}
        />
        <StatCard
          label="High Anomalies"
          value={summary?.high_anomalies || 0}
          icon={<Zap className="w-4 h-4" />}
          color="red"
          alert={!!summary?.high_anomalies}
        />
        <StatCard
          label="Inspections Today"
          value={summary?.inspections_today || 0}
          icon={<Search className="w-4 h-4" />}
          color="teal"
        />
        <StatCard
          label="Open Findings"
          value={summary?.open_findings || 0}
          icon={<ClipboardCheck className="w-4 h-4" />}
          color="amber"
        />
        <StatCard
          label="Cameras Offline"
          value={summary?.cameras_offline || 0}
          icon={<Camera className="w-4 h-4" />}
          color={summary?.cameras_offline ? 'red' : 'green'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Hero Project Card — always visible front-and-center */}
        {hero && (
          <div className="lg:col-span-1">
    <div className="card relative overflow-hidden shadow-[0_8px_40px_-12px_rgba(249,115,22,0.3)] border-orange-200/50 hover:border-orange-300 transition-all duration-300">
      <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-orange-400 via-red-500 to-orange-400"></div>
      <div className="absolute -top-24 -right-24 w-48 h-48 bg-orange-400/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="card-header bg-gradient-to-b from-orange-50/50 to-transparent border-b-orange-100/50 flex items-center gap-2 relative z-10">
        <div className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
        </div>
        <span className="font-bold text-slate-800 tracking-wide uppercase text-sm">Priority Alert</span>
        <span className="ml-auto text-[10px] tracking-wider text-orange-700 font-bold bg-orange-200/50 px-2 py-1 rounded border border-orange-300/30">
          SYSTEM HERO
        </span>
      </div>
      <div className="p-6 space-y-5 relative z-10">
        <div className="flex items-start gap-4">
          <div className="relative">
             <div className="absolute -inset-1 bg-gradient-to-tr from-orange-400 to-red-500 rounded-full blur opacity-30"></div>
             <HealthIndexRing score={hero.health_index} size="md" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-slate-900 text-lg leading-tight truncate">
              {hero.project_name}
            </h3>
            <p className="text-sm text-slate-500 mt-1">{hero.district}, {hero.state}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <StatusBadge status={hero.status} size="sm" />
              <StatusBadge status={hero.risk_level} size="sm" />
            </div>
          </div>
        </div>

                {/* Anomaly reasons */}
                {heroAnomaly && (
                  <div className="bg-white/50 backdrop-blur-sm border border-orange-200/60 shadow-[inset_0_2px_10px_rgba(255,237,213,0.5)] rounded-xl p-4 space-y-3 relative overflow-hidden group hover:border-orange-300 transition-colors">
                    <div className="absolute top-0 right-0 p-4 opacity-5 transform group-hover:scale-110 transition-transform duration-500 pointer-events-none">
                      <Zap className="w-12 h-12" aria-hidden />
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="bg-orange-100 p-1.5 rounded-md">
                        <Zap className="w-4 h-4 text-orange-600" aria-hidden />
                      </div>
                      <span className="text-sm font-bold text-orange-800 tracking-wide">
                        Anomaly Score: <span className="text-red-600">{heroAnomaly.anomaly_score}</span>/100
                      </span>
                    </div>
                    <div className="space-y-2">
                      {Object.values(heroAnomaly.reasons).slice(0, 4).map((reason: any, i: number) => (
                        <div key={i} className="flex items-center gap-2.5 text-sm text-slate-700 bg-white/60 py-1.5 px-2.5 rounded-lg border border-slate-100 shadow-sm">
                          <span className="w-2 h-2 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex-shrink-0" aria-hidden />
                          <span className="font-medium truncate">{reason.label}</span>
                          <span className="ml-auto font-mono font-bold text-orange-600">+{reason.score?.toFixed(1)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/60 rounded-xl px-4 py-3 flex items-center justify-between shadow-sm">
                  <div>
                    <div className="text-[10px] font-bold tracking-widest text-amber-600 uppercase mb-0.5">SYSTEM RECOMMENDATION</div>
                    <div className="text-sm font-bold text-slate-800">
                      Surprise Inspection Required
                    </div>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center shadow-sm border border-amber-100 text-amber-600">
                    <ClipboardCheck className="w-4 h-4" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <button
                    onClick={() => navigate(`/projects/${hero.id}`)}
                    className="btn-secondary text-sm py-2.5 justify-center shadow-sm"
                  >
                    <Eye className="w-4 h-4" aria-hidden />
                    View Case
                  </button>
                  <button
                    onClick={() => navigate(`/inspections/assign/${hero.id}`)}
                    className="btn-primary text-sm py-2.5 justify-center"
                  >
                    <Search className="w-4 h-4" aria-hidden />
                    Initiate Action
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Alert list */}
        <div className="lg:col-span-2 space-y-3">
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-500" aria-hidden />
                <span className="font-semibold text-slate-800">Active Anomaly Alerts</span>
              </div>
              <span className="text-xs text-slate-500">{topAlerts.length} unacknowledged</span>
            </div>
            <div className="divide-y divide-slate-100">
              {topAlerts.length === 0 ? (
                <div className="p-5 text-center text-sm text-slate-400">No active alerts</div>
              ) : (
                topAlerts.map((alert) => (
                  <AlertRow key={alert.id} alert={alert} onView={() => navigate(`/projects/${alert.project_id}`)} />
                ))
              )}
            </div>
          </div>

          {/* Health distribution */}
          {dashboardData && (
            <div className="card">
              <div className="card-header">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-brand-600" aria-hidden />
                  <span className="font-semibold text-slate-800">Health Distribution</span>
                </div>
              </div>
              <div className="p-4 grid grid-cols-4 gap-3">
                <DistributionBar
                  label="Healthy"
                  value={dashboardData.health_distribution?.healthy || 0}
                  total={summary?.total_projects || 1}
                  color="bg-emerald-500"
                />
                <DistributionBar
                  label="Watch"
                  value={dashboardData.health_distribution?.watch || 0}
                  total={summary?.total_projects || 1}
                  color="bg-amber-500"
                />
                <DistributionBar
                  label="Attention"
                  value={dashboardData.health_distribution?.high_attention || 0}
                  total={summary?.total_projects || 1}
                  color="bg-orange-500"
                />
                <DistributionBar
                  label="Critical"
                  value={dashboardData.health_distribution?.critical || 0}
                  total={summary?.total_projects || 1}
                  color="bg-red-500"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon,
  color,
  alert,
}: {
  label: string
  value: number
  icon: React.ReactNode
  color: 'blue' | 'orange' | 'red' | 'teal' | 'amber' | 'green'
  alert?: boolean
}) {
  const colors = {
    blue: 'text-blue-600 bg-blue-50',
    orange: 'text-orange-600 bg-orange-50',
    red: 'text-red-600 bg-red-50',
    teal: 'text-teal-600 bg-teal-50',
    amber: 'text-amber-600 bg-amber-50',
    green: 'text-green-600 bg-green-50',
  }

  return (
    <div className={clsx('stat-card group', alert && 'ring-1 ring-orange-300')}>
      <div className="flex items-center justify-between mb-2">
        <div className={clsx('p-1.5 rounded-md', colors[color])} aria-hidden>
          {icon}
        </div>
        {alert && value > 0 && (
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" aria-hidden />
        )}
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  )
}

function AlertRow({ alert, onView }: { alert: AnomalyEvent; onView: () => void }) {
  const reasons = Object.values(alert.reasons) as any[]
  return (
    <div className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors">
      <div
        className={clsx(
          'w-2 flex-shrink-0 self-stretch rounded-full',
          alert.severity === 'CRITICAL' ? 'bg-red-500' :
          alert.severity === 'HIGH' ? 'bg-orange-500' :
          alert.severity === 'MEDIUM' ? 'bg-amber-500' : 'bg-blue-500'
        )}
        aria-hidden
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-900 truncate">{alert.project_name}</span>
          <StatusBadge status={alert.severity} size="sm" />
        </div>
        <div className="text-xs text-slate-500 mt-0.5">
          Score: {alert.anomaly_score}/100 — {reasons[0]?.label}
          {reasons.length > 1 && ` +${reasons.length - 1} more`}
        </div>
        <div className="text-xs text-slate-400">
          {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
        </div>
      </div>
      <button
        onClick={onView}
        className="btn-secondary text-xs py-1 px-2 flex-shrink-0"
        aria-label={`View ${alert.project_name}`}
      >
        View
        <ChevronRight className="w-3 h-3" aria-hidden />
      </button>
    </div>
  )
}

function DistributionBar({
  label, value, total, color
}: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return (
    <div className="text-center">
      <div className="text-lg font-bold text-slate-900">{value}</div>
      <div className="h-1.5 bg-slate-100 rounded-full my-1.5 overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all', color)}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${label}: ${pct}%`}
        />
      </div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  )
}
