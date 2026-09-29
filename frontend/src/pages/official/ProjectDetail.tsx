/**
 * Project Detail — full view with health, anomaly, CCTV, attendance, inspections.
 */
import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, MapPin, Calendar, Users, Camera, AlertTriangle,
  Search, Activity, ChevronDown, ChevronUp, Play, TrendingUp,
  ShieldCheck
} from 'lucide-react'
import { projectsApi, monitoringApi, cctvApi, analyticsApi } from '../../services/api'
import { HealthIndexRing } from '../../components/shared/HealthIndexRing'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { WhyExplainer } from '../../components/shared/WhyExplainer'
import { DemoBanner } from '../../components/shared/DemoBanner'
import { PageLoader } from '../../components/shared/LoadingSpinner'
import { format } from 'date-fns'
import type { Project, AnomalyEvent } from '../../types'

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const projectId = parseInt(id || '0')

  const { data: project, isLoading } = useQuery<Project>({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId).then((r) => r.data),
  })

  const { data: healthData } = useQuery({
    queryKey: ['health', projectId],
    queryFn: () => monitoringApi.health(projectId).then((r) => r.data),
  })

  const { data: anomalies } = useQuery<AnomalyEvent[]>({
    queryKey: ['anomalies', projectId],
    queryFn: () => monitoringApi.anomalies(projectId).then((r) => r.data),
  })

  const { data: cameras } = useQuery({
    queryKey: ['cameras', projectId],
    queryFn: () => cctvApi.list(projectId).then((r) => r.data),
  })

  const { data: attendanceData } = useQuery({
    queryKey: ['attendance', projectId],
    queryFn: () => analyticsApi.attendance(projectId, 30).then((r) => r.data),
  })

  const runAnomaly = useMutation({
    mutationFn: () => analyticsApi.runAnomaly(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['anomalies', projectId] })
      qc.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  if (isLoading || !project) return <PageLoader label="Loading project..." />

  const latestAnomaly = anomalies?.[0]
  const healthScore = healthData?.latest

  const whyReasons = latestAnomaly
    ? Object.values(latestAnomaly.reasons).map((r: any) => ({
        label: r.label,
        score: r.score,
        evidence: r.evidence,
        threshold: r.threshold,
      }))
    : []

  const healthReasons = healthScore?.explanation
    ? Object.entries(healthScore.explanation)
        .filter(([k]) => !['weights', 'label', 'disclaimer'].includes(k))
        .map(([k, v]: [string, any]) => ({
          label: k.charAt(0).toUpperCase() + k.slice(1),
          score: v.score,
          evidence: `${v.score}/${v.max} — ${v.reason || ''}`,
        }))
    : []

  return (
    <div className="p-5 space-y-5 max-w-screen-xl mx-auto">
      {/* Back + Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="btn-secondary py-1.5"
          aria-label="Go back"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden />
          Back
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-lg font-bold text-slate-900 truncate">{project.project_name}</h1>
            {project.is_hero_project && (
              <span className="badge bg-teal-100 text-teal-800">Hero Demo</span>
            )}
            <DemoBanner inline />
          </div>
          <div className="flex items-center gap-1 text-sm text-slate-500 mt-0.5">
            <MapPin className="w-3.5 h-3.5" aria-hidden />
            {project.district}, {project.state} — {project.scheme}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => runAnomaly.mutate()}
            disabled={runAnomaly.isPending}
            className="btn-secondary text-sm"
          >
            <Activity className="w-4 h-4" aria-hidden />
            {runAnomaly.isPending ? 'Analyzing...' : 'Run Analysis'}
          </button>
          {(project.risk_level === 'HIGH' || project.risk_level === 'CRITICAL') && (
            <button
              onClick={() => navigate(`/inspections/assign/${projectId}`)}
              className="btn-primary text-sm bg-orange-600 hover:bg-orange-700"
            >
              <Search className="w-4 h-4" aria-hidden />
              Initiate Inspection
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left: Health + Anomaly */}
        <div className="space-y-4">
          {/* Health Index Card */}
          <div className="card p-5">
            <div className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-3">
              Composite Monitoring Health Index — Prototype
            </div>
            <div className="flex items-center gap-4">
              <HealthIndexRing score={project.health_index} size="lg" />
              <div>
                <div className="text-sm text-slate-500">Status</div>
                <StatusBadge status={project.status} />
                <div className="text-xs text-slate-400 mt-1">{project.scheme}</div>
              </div>
            </div>

            {healthScore && (
              <div className="mt-4 space-y-1.5">
                <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Score Breakdown</div>
                {[
                  { k: 'Attendance', v: healthScore.attendance_score, max: 25 },
                  { k: 'Reporting', v: healthScore.reporting_score, max: 20 },
                  { k: 'Inspection', v: healthScore.inspection_score, max: 20 },
                  { k: 'Evidence', v: healthScore.evidence_score, max: 15 },
                  { k: 'Timeliness', v: healthScore.timeliness_score, max: 10 },
                  { k: 'Findings', v: healthScore.findings_score, max: 10 },
                ].map((item) => (
                  <div key={item.k} className="flex items-center gap-2 text-xs">
                    <span className="w-20 text-slate-600 text-right">{item.k}</span>
                    <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-500 rounded-full"
                        style={{ width: `${(item.v / item.max) * 100}%` }}
                        role="progressbar"
                        aria-valuenow={item.v}
                        aria-valuemax={item.max}
                      />
                    </div>
                    <span className="w-14 font-mono text-slate-700 text-right">
                      {item.v.toFixed(1)}/{item.max}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-3">
              <WhyExplainer
                triggerLabel="WHY THIS SCORE?"
                reasons={healthReasons}
                variant="health"
                methodology="Composite rule-based scoring across 6 weighted dimensions"
                disclaimer={healthScore?.explanation?.disclaimer}
              />
            </div>
          </div>

          {/* Project info */}
          <div className="card p-4 space-y-2.5">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Project Details</div>
            <InfoRow icon={<Users />} label="Beneficiaries" value={project.beneficiary_count} />
            <InfoRow icon={<Users />} label="Staff" value={project.staff_count} />
            <InfoRow icon={<MapPin />} label="Type" value={project.project_type} />
            <InfoRow
              icon={<Calendar />}
              label="Last Inspection"
              value={project.last_inspection ? format(new Date(project.last_inspection), 'dd MMM yyyy') : 'Never'}
            />
            <InfoRow
              icon={<Calendar />}
              label="Last Report"
              value={project.last_report ? format(new Date(project.last_report), 'dd MMM yyyy') : 'None'}
            />
          </div>
        </div>

        {/* Right: Anomaly + CCTV + Attendance */}
        <div className="lg:col-span-2 space-y-4">
          {/* Anomaly card */}
          {latestAnomaly && (
            <div className="card border-orange-200">
              <div className="card-header flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-600" aria-hidden />
                <span className="font-semibold text-slate-800">Anomaly Intelligence</span>
                <StatusBadge status={latestAnomaly.severity} size="sm" className="ml-auto" />
              </div>
              <div className="p-4 space-y-3">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-orange-700">{latestAnomaly.anomaly_score}</div>
                    <div className="text-xs text-slate-500">/ 100</div>
                    <div className="text-xs font-semibold text-orange-600 mt-0.5">Anomaly Score</div>
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-slate-800 mb-1">
                      Recommended: {latestAnomaly.recommended_action.replace('_', ' ')}
                    </div>
                    <div className="text-xs text-amber-700 font-medium bg-amber-50 border border-amber-200 rounded px-2 py-1">
                      POTENTIAL DISCREPANCY — HUMAN VERIFICATION REQUIRED
                    </div>
                  </div>
                </div>

                <WhyExplainer
                  triggerLabel="WHY THIS ALERT?"
                  title="Anomaly Contributors"
                  reasons={whyReasons}
                  variant="anomaly"
                  methodology="Rule-based thresholds + statistical deviation (z-score)"
                  disclaimer="These are indicators, not conclusions. Official review required before action."
                />
              </div>
            </div>
          )}

          {/* CCTV Status */}
          <div className="card">
            <div className="card-header flex items-center gap-2">
              <Camera className="w-4 h-4 text-slate-600" aria-hidden />
              <span className="font-semibold text-slate-800">CCTV Monitoring</span>
            </div>
            <div className="p-4">
              {!cameras || cameras.length === 0 ? (
                <p className="text-sm text-slate-400">No cameras configured</p>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {cameras.map((cam: any) => (
                    <div
                      key={cam.id}
                      className="border rounded-md p-3 space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-700">{cam.camera_name}</span>
                        <StatusBadge status={cam.status} size="sm" />
                      </div>
                      <div className="text-xs text-slate-500">{cam.location_description}</div>
                      <div className="text-xs text-amber-700 font-medium">{cam.label}</div>
                      {cam.last_heartbeat && (
                        <div className="text-xs text-slate-400">
                          Last seen: {format(new Date(cam.last_heartbeat), 'HH:mm, dd MMM')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Attendance Analytics */}
          {attendanceData && (
            <div className="card">
              <div className="card-header flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-slate-600" aria-hidden />
                <span className="font-semibold text-slate-800">Attendance Analytics (30 days)</span>
              </div>
              <div className="p-4 space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center">
                    <div className="text-xl font-bold text-slate-900">{attendanceData.latest_reported ?? '—'}</div>
                    <div className="text-xs text-slate-500">Latest Reported</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-slate-900">{attendanceData.expected_count}</div>
                    <div className="text-xs text-slate-500">Expected</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-orange-600">{attendanceData.anomaly_days_in_period}</div>
                    <div className="text-xs text-slate-500">Anomaly Days</div>
                  </div>
                </div>
                <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1.5">
                  {attendanceData.disclaimer}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: any }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-4 h-4 text-slate-400 flex-shrink-0" aria-hidden>{icon}</span>
      <span className="text-slate-500 w-28 flex-shrink-0">{label}</span>
      <span className="text-slate-800 font-medium">{value}</span>
    </div>
  )
}
