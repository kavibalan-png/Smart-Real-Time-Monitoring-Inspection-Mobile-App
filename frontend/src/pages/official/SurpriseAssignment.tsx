/**
 * Surprise Inspection Assignment page.
 * Shows controlled assignment pipeline — never exposes full candidate pool.
 */
import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  ArrowLeft, Shield, Zap, CheckCircle2, AlertTriangle, User,
  MapPin, Clock, Lock, Info
} from 'lucide-react'
import { projectsApi, inspectionsApi, monitoringApi } from '../../services/api'
import { StatusBadge } from '../../components/shared/StatusBadge'
import { WhyExplainer } from '../../components/shared/WhyExplainer'
import { PageLoader } from '../../components/shared/LoadingSpinner'
import { format } from 'date-fns'

export function SurpriseAssignment() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [assignment, setAssignment] = useState<any>(null)
  const [recommendation, setRecommendation] = useState<any>(null)
  const [step, setStep] = useState<'review' | 'assign' | 'done'>('review')
  const pid = parseInt(projectId || '0')

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', pid],
    queryFn: () => projectsApi.get(pid).then((r) => r.data),
  })

  const { data: anomalies } = useQuery({
    queryKey: ['anomalies', pid],
    queryFn: () => monitoringApi.anomalies(pid).then((r) => r.data),
    enabled: !!pid,
  })

  const getRecommendation = useMutation({
    mutationFn: () => inspectionsApi.recommend(pid),
    onSuccess: (resp) => {
      setRecommendation(resp.data)
      setStep('assign')
    },
  })

  const assignInspection = useMutation({
    mutationFn: () =>
      inspectionsApi.assign({
        project_id: pid,
        anomaly_event_id: anomalies?.[0]?.id || null,
        max_distance_km: 150,
      }),
    onSuccess: (resp) => {
      setAssignment(resp.data)
      setStep('done')
    },
  })

  if (isLoading || !project) return <PageLoader label="Loading..." />

  const latestAnomaly = anomalies?.[0]
  const whyReasons = latestAnomaly
    ? Object.values(latestAnomaly.reasons).map((r: any) => ({
        label: r.label,
        score: r.score,
        evidence: r.evidence,
      }))
    : []

  return (
    <div className="p-5 max-w-2xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-secondary py-1.5" aria-label="Go back">
          <ArrowLeft className="w-4 h-4" aria-hidden />
          Back
        </button>
        <h1 className="text-lg font-bold text-slate-900">Surprise Inspection Assignment</h1>
      </div>

      {/* Project summary */}
      <div className="card p-4">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="font-semibold text-slate-900">{project.project_name}</div>
            <div className="text-sm text-slate-500">{project.district}, {project.state}</div>
            <div className="flex gap-1.5 mt-1.5">
              <StatusBadge status={project.status} size="sm" />
              <StatusBadge status={project.risk_level} size="sm" />
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900">{project.health_index}</div>
            <div className="text-xs text-slate-500">/ 100</div>
            <div className="text-xs font-medium text-slate-600">Health Index</div>
          </div>
        </div>
      </div>

      {/* Anomaly WHY */}
      {latestAnomaly && step === 'review' && (
        <div className="card border-orange-200">
          <div className="card-header flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-600" aria-hidden />
            <span className="font-semibold text-slate-800">WHY THIS PROJECT?</span>
            <span className="ml-auto font-mono font-bold text-orange-700">
              Score: {latestAnomaly.anomaly_score}/100
            </span>
          </div>
          <div className="p-4">
            <WhyExplainer
              triggerLabel="WHY NOW?"
              title="Anomaly Reasons"
              reasons={whyReasons}
              variant="anomaly"
              disclaimer="POTENTIAL DISCREPANCY — HUMAN VERIFICATION REQUIRED"
              methodology="Rule-based thresholds + statistical deviation"
            />
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-3 py-2">
              <Info className="w-3.5 h-3.5 flex-shrink-0" aria-hidden />
              <span>This is a system recommendation. The official decides whether to proceed.</span>
            </div>
          </div>
        </div>
      )}

      {/* Security notice */}
      <div className="card p-4 bg-navy-700 text-white border-0">
        <div className="flex items-center gap-2 mb-2">
          <Lock className="w-4 h-4" aria-hidden />
          <span className="font-semibold text-sm">Assignment Security</span>
        </div>
        <ul className="text-xs text-slate-300 space-y-1">
          <li>• Inspector selection is performed server-side only</li>
          <li>• Candidate pool is never transmitted to this browser</li>
          <li>• Cryptographically strong randomization (secrets.choice)</li>
          <li>• Assignment is confidential until inspection date</li>
          <li>• Full audit trail is maintained</li>
        </ul>
      </div>

      {/* Step: Review → Assign → Done */}
      {step === 'review' && (
        <div className="space-y-3">
          <div className="text-sm text-slate-700 font-medium">
            Confirm to proceed with surprise inspection recommendation:
          </div>
          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => navigate(-1)} className="btn-secondary">
              Cancel
            </button>
            <button
              onClick={() => getRecommendation.mutate()}
              disabled={getRecommendation.isPending}
              className="btn-primary bg-orange-600 hover:bg-orange-700"
            >
              <Zap className="w-4 h-4" aria-hidden />
              {getRecommendation.isPending ? 'Loading...' : 'Review Recommendation'}
            </button>
          </div>
        </div>
      )}

      {step === 'assign' && recommendation && (
        <div className="space-y-4">
          <div className="card p-4 bg-amber-50 border-amber-200">
            <div className="text-sm font-bold text-amber-800 mb-2">SYSTEM RECOMMENDATION</div>
            <div className="text-base font-semibold text-slate-900">
              {recommendation.recommendation.replace(/_/g, ' ')}
            </div>
            <div className="text-xs text-amber-700 mt-1">{recommendation.disclaimer}</div>
          </div>

          <div className="card p-4">
            <div className="font-semibold text-slate-800 mb-3">Official Decision Required</div>
            <div className="text-sm text-slate-600 mb-4">
              Clicking <strong>Initiate Surprise Inspection</strong> will trigger the secure
              server-side assignment pipeline. The selected inspector will receive a notification
              but project identity remains confidential until inspection day.
            </div>
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => setStep('review')} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={() => assignInspection.mutate()}
                disabled={assignInspection.isPending}
                className="btn-primary bg-orange-600 hover:bg-orange-700"
              >
                <Shield className="w-4 h-4" aria-hidden />
                {assignInspection.isPending ? 'Assigning...' : 'Initiate Surprise Inspection'}
              </button>
            </div>
          </div>
        </div>
      )}

      {step === 'done' && assignment && (
        <div className="space-y-4">
          <div className="card p-5 bg-emerald-50 border-emerald-200 text-center">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-2" aria-hidden />
            <div className="text-lg font-bold text-emerald-800">Inspection Assigned</div>
            <div className="text-sm text-slate-600 mt-1">
              Inspector has been notified securely
            </div>
          </div>

          <div className="card p-4 space-y-3">
            <div className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
              Assignment Details
            </div>
            <AssignRow icon={<Shield />} label="Assignment ID" value={assignment.assignment_id} mono />
            <AssignRow icon={<User />} label="Assigned Inspector" value={assignment.inspector_name} />
            <AssignRow icon={<Clock />} label="Assigned At" value={format(new Date(assignment.assigned_at), 'dd MMM yyyy, HH:mm')} />
            <AssignRow icon={<Zap />} label="Algorithm" value={assignment.selection_algorithm} mono />
            <AssignRow icon={<Zap />} label="Pool Size" value={`${assignment.candidate_pool_size} eligible inspectors`} />

            <div className="mt-2">
              <WhyExplainer
                triggerLabel="WHY THIS INSPECTOR?"
                title="Selection Rationale"
                reasons={[
                  { label: 'Inspector is available', evidence: 'Availability confirmed' },
                  { label: 'Workload within limits', evidence: 'Below maximum assignment threshold' },
                  { label: 'Geographic compatibility', evidence: 'Within 150km of project' },
                  { label: 'Secure random selection', evidence: `Selected from ${assignment.candidate_pool_size} eligible candidates` },
                ]}
                variant="assignment"
                methodology="Eligibility → Availability → Workload → Geography → Secure random (secrets.choice)"
              />
            </div>
          </div>

          <button
            onClick={() => navigate('/inspections')}
            className="btn-primary w-full justify-center"
          >
            View Inspections
          </button>
        </div>
      )}
    </div>
  )
}

function AssignRow({ icon, label, value, mono }: { icon: React.ReactNode; label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-4 h-4 text-slate-400 flex-shrink-0" aria-hidden>{icon}</span>
      <span className="text-slate-500 w-36 flex-shrink-0">{label}</span>
      <span className={`text-slate-800 font-medium ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}
