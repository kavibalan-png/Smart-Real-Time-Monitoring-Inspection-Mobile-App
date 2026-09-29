/**
 * Evidence Integrity Badge — displays SHA-256 verification result.
 * Clear labeling: "EVIDENCE INTEGRITY VERIFICATION" — not "blockchain" or "tamper-proof".
 */
import React from 'react'
import { ShieldCheck, ShieldAlert, HelpCircle } from 'lucide-react'
import clsx from 'clsx'

interface Props {
  result?: 'VERIFIED' | 'MISMATCH' | 'ERROR' | null
  hash?: string | null
  showHash?: boolean
  className?: string
}

export function EvidenceIntegrityBadge({ result, hash, showHash = false, className }: Props) {
  if (!result) {
    return (
      <div className={clsx('inline-flex items-center gap-1.5 text-slate-500 text-sm', className)}>
        <HelpCircle className="w-4 h-4" aria-hidden />
        <span>Not verified</span>
      </div>
    )
  }

  if (result === 'VERIFIED') {
    return (
      <div className={clsx('space-y-1', className)}>
        <div className="integrity-verified">
          <ShieldCheck className="w-4 h-4" aria-hidden />
          <span>EVIDENCE INTEGRITY VERIFIED</span>
        </div>
        {showHash && hash && (
          <p className="text-xs font-mono text-slate-500 break-all pl-5">
            SHA-256: {hash}
          </p>
        )}
        <p className="text-xs text-slate-500 pl-5">
          File bytes match stored fingerprint
        </p>
      </div>
    )
  }

  if (result === 'MISMATCH') {
    return (
      <div className={clsx('space-y-1', className)}>
        <div className="integrity-mismatch">
          <ShieldAlert className="w-4 h-4" aria-hidden />
          <span>⚠ INTEGRITY MISMATCH</span>
        </div>
        <p className="text-xs text-red-600 pl-5">
          Hash mismatch detected — file may have been modified
        </p>
      </div>
    )
  }

  return (
    <div className={clsx('inline-flex items-center gap-1.5 text-slate-500 text-sm', className)}>
      <HelpCircle className="w-4 h-4" aria-hidden />
      <span>Verification error</span>
    </div>
  )
}
