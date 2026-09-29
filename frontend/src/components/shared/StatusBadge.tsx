import React from 'react'
import clsx from 'clsx'

interface Props {
  status: string
  size?: 'sm' | 'md'
  className?: string
}

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  // Project/Risk
  LOW: { label: 'Low Risk', className: 'badge-low' },
  MEDIUM: { label: 'Medium', className: 'badge-medium' },
  HIGH: { label: 'High Risk', className: 'badge-high' },
  CRITICAL: { label: 'Critical', className: 'badge-critical' },
  // Project Status
  MONITORING: { label: 'Monitoring', className: 'badge bg-blue-100 text-blue-800' },
  WATCH: { label: 'Watch', className: 'badge-watch' },
  HIGH_ATTENTION: { label: 'High Attention', className: 'badge-attention' },
  INSPECTION_REQUIRED: { label: 'Inspection Required', className: 'badge-high' },
  UNDER_REVIEW: { label: 'Under Review', className: 'badge bg-purple-100 text-purple-800' },
  ACTION_REQUIRED: { label: 'Action Required', className: 'badge-critical' },
  RESOLVED: { label: 'Resolved', className: 'badge-healthy' },
  CLOSED: { label: 'Closed', className: 'badge bg-slate-100 text-slate-600' },
  // Inspection
  ASSIGNED: { label: 'Assigned', className: 'badge bg-blue-100 text-blue-800' },
  IN_PROGRESS: { label: 'In Progress', className: 'badge bg-indigo-100 text-indigo-800' },
  SUBMITTED: { label: 'Submitted', className: 'badge bg-teal-100 text-teal-800' },
  APPROVED: { label: 'Approved', className: 'badge-healthy' },
  REINSPECTION: { label: 'Reinspection', className: 'badge-high' },
  ESCALATED: { label: 'Escalated', className: 'badge-critical' },
  // CCTV
  LIVE: { label: 'Live', className: 'badge-healthy' },
  OFFLINE: { label: 'Offline', className: 'badge-critical' },
  DEGRADED: { label: 'Degraded', className: 'badge-high' },
  // Attendance
  NORMAL: { label: 'Normal', className: 'badge-healthy' },
  ANOMALY: { label: 'Anomaly', className: 'badge-high' },
  // Evidence
  VERIFIED: { label: '✓ Verified', className: 'badge bg-emerald-100 text-emerald-800' },
  MISMATCH: { label: '⚠ Mismatch', className: 'badge-critical' },
  // Severity
  INFO: { label: 'Info', className: 'badge bg-slate-100 text-slate-600' },
}

export function StatusBadge({ status, size = 'md', className }: Props) {
  const config = STATUS_MAP[status] || { label: status, className: 'badge bg-slate-100 text-slate-600' }
  return (
    <span
      className={clsx(config.className, size === 'sm' && 'text-xs py-0', className)}
      role="status"
      aria-label={config.label}
    >
      {config.label}
    </span>
  )
}
