// Core type definitions for the AIIP frontend

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  district: string | null
  state: string | null
  is_demo: boolean
}

export type UserRole =
  | 'SUPER_ADMIN'
  | 'DEPARTMENT_OFFICIAL'
  | 'PMU_OFFICER'
  | 'INSPECTION_OFFICER'
  | 'PROJECT_ADMIN'
  | 'PROJECT_STAFF'
  | 'CITIZEN'

export interface Project {
  id: number
  project_code: string
  project_name: string
  scheme: string
  district: string
  state: string
  address: string | null
  latitude: number
  longitude: number
  beneficiary_count: number
  staff_count: number
  project_type: string
  health_index: number
  risk_level: RiskLevel
  status: ProjectStatus
  attendance_status: string
  cctv_status: string
  compliance_status: string
  open_findings: number
  last_inspection: string | null
  last_report: string | null
  is_demo: boolean
  is_hero_project: boolean
  created_at: string
  updated_at: string
}

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type ProjectStatus =
  | 'MONITORING'
  | 'WATCH'
  | 'HIGH_ATTENTION'
  | 'INSPECTION_REQUIRED'
  | 'UNDER_REVIEW'
  | 'ACTION_REQUIRED'
  | 'RESOLVED'
  | 'CLOSED'

export interface MonitoringSummary {
  total_projects: number
  attention_required: number
  high_anomalies: number
  inspections_today: number
  open_findings: number
  pending_followup: number
  cameras_offline: number
  healthy_projects: number
  watch_projects: number
  critical_projects: number
}

export interface AnomalyEvent {
  id: number
  project_id: number
  project_name: string
  anomaly_score: number
  severity: RiskLevel
  reasons: Record<string, AnomalyReason>
  recommended_action: string
  algorithm_version: string
  is_acknowledged: boolean
  created_at: string
}

export interface AnomalyReason {
  label: string
  score: number
  evidence: string
  threshold: string
}

export interface HealthScore {
  total_score: number
  status: string
  attendance_score: number
  reporting_score: number
  inspection_score: number
  evidence_score: number
  timeliness_score: number
  findings_score: number
  explanation: Record<string, any>
  computed_at: string
}

export interface Inspection {
  id: number
  inspection_code: string
  project_id: number
  project_name: string
  inspector_id: number
  status: InspectionStatus
  inspection_type: string
  start_time: string | null
  end_time: string | null
  start_latitude: number | null
  start_longitude: number | null
  gps_accuracy: number | null
  offline_captured: boolean
  overall_rating: string | null
  summary_notes: string | null
  recommendations: string | null
  official_decision: string | null
  decision_notes: string | null
  checklist: ChecklistItem[]
  findings: Finding[]
  evidence: EvidenceItem[]
  created_at: string
}

export type InspectionStatus =
  | 'ASSIGNED'
  | 'NOTIFIED'
  | 'ACKNOWLEDGED'
  | 'IN_PROGRESS'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'REINSPECTION'
  | 'ESCALATED'
  | 'CLOSED'

export interface ChecklistItem {
  id: number
  category: string
  item_key: string
  item_label: string
  value: string | null
  observation: string | null
  is_critical: boolean
}

export type ChecklistValue = 'PASS' | 'FAIL' | 'PARTIAL' | 'NOT_OBSERVED'

export interface Finding {
  id: number
  finding_code: string
  category: string
  description: string
  severity: RiskLevel
  status: string
}

export interface EvidenceItem {
  id: number
  evidence_code: string
  evidence_type: string
  latitude: number | null
  longitude: number | null
  gps_confidence: string
  captured_at: string
  captured_offline: boolean
  sha256_hash: string | null
  description: string | null
}

export interface Assignment {
  id: number
  assignment_id: string
  project_id: number
  project_name: string
  inspector_id: number
  inspector_name: string
  assigned_by: number
  selection_algorithm: string
  ruleset_version: string
  candidate_pool_size: number
  eligibility_reasons: Record<string, any>
  status: string
  assigned_at: string
  is_demo: boolean
}

export interface Notification {
  id: number
  notification_type: string
  title: string
  message: string
  priority: string
  resource_type: string | null
  resource_id: number | null
  is_read: boolean
  created_at: string
}

export interface Followup {
  id: number
  followup_code: string
  project_id: number
  inspection_id: number | null
  action_type: string
  description: string
  due_date: string | null
  status: string
  resolution_notes: string | null
  resolved_at: string | null
  created_at: string
}

export interface TimelineEvent {
  timestamp: string
  event_type: string
  description: string
  actor: string | null
  resource_type: string | null
  resource_id: number | null
}

export interface Camera {
  id: number
  project_id: number
  camera_name: string
  location_description: string | null
  status: 'LIVE' | 'OFFLINE' | 'DEGRADED'
  demo_video_url: string | null
  last_heartbeat: string | null
  is_demo: boolean
  label: string
}

// Offline sync types
export interface OfflineOperation {
  local_id: string
  operation_type: string
  payload: Record<string, any>
  created_at: string
  sync_status: 'PENDING' | 'UPLOADING' | 'SUCCESS' | 'FAILED' | 'RETRY'
  retry_count: number
}
