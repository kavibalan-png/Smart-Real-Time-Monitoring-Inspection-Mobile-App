/**
 * Offline synchronization service.
 * Processes the offline operation queue when connectivity returns.
 * Implements idempotency via local_id deduplication.
 */
import {
  getPendingOperations,
  updateOperationStatus,
  getPendingEvidenceFiles,
} from './offlineDB'
import api, { evidenceApi } from '../services/api'

export type SyncProgressCallback = (
  processed: number,
  total: number,
  current: string
) => void

export async function syncPendingOperations(
  onProgress?: SyncProgressCallback
): Promise<{ success: number; failed: number; errors: string[] }> {
  const pending = await getPendingOperations()
  let success = 0
  let failed = 0
  const errors: string[] = []

  for (let i = 0; i < pending.length; i++) {
    const op = pending[i]
    onProgress?.(i, pending.length, op.operation_type)

    try {
      await updateOperationStatus(op.local_id, 'UPLOADING')

      switch (op.operation_type) {
        case 'CHECKLIST_UPDATE':
          await api.post(
            `/inspections/${op.payload.inspection_id}/checklist`,
            op.payload
          )
          break
        case 'INSPECTION_SUBMIT':
          await api.post(
            `/inspections/${op.payload.inspection_id}/submit`,
            op.payload
          )
          break
        case 'GPS_CAPTURE':
          await api.post(
            `/inspections/${op.payload.inspection_id}/gps`,
            op.payload
          )
          break
        default:
          // Generic operation — POST to appropriate endpoint
          await api.post(`/${op.operation_type.toLowerCase()}`, op.payload)
      }

      await updateOperationStatus(op.local_id, 'SUCCESS')
      success++
    } catch (error: any) {
      const isRetryable =
        !error.response || error.response.status >= 500 || error.code === 'ECONNABORTED'

      if (isRetryable && op.retry_count < 3) {
        await updateOperationStatus(op.local_id, 'RETRY')
      } else {
        await updateOperationStatus(op.local_id, 'FAILED')
        failed++
        errors.push(`${op.operation_type}: ${error.message || 'Unknown error'}`)
      }
    }
  }

  onProgress?.(pending.length, pending.length, 'Complete')
  return { success, failed, errors }
}

export async function syncEvidenceFiles(
  inspectionId: number,
  onProgress?: SyncProgressCallback
): Promise<{ success: number; failed: number }> {
  const pending = await getPendingEvidenceFiles(inspectionId)
  let success = 0
  let failed = 0

  for (let i = 0; i < pending.length; i++) {
    const item = pending[i]
    onProgress?.(i, pending.length, 'Evidence file')

    try {
      const formData = new FormData()
      formData.append('file', item.file_data, item.metadata.filename || 'evidence.jpg')
      formData.append('inspection_id', String(inspectionId))
      if (item.metadata.latitude) formData.append('latitude', String(item.metadata.latitude))
      if (item.metadata.longitude) formData.append('longitude', String(item.metadata.longitude))
      if (item.metadata.gps_accuracy) formData.append('gps_accuracy', String(item.metadata.gps_accuracy))
      formData.append('captured_offline', 'true')
      formData.append('evidence_type', item.metadata.evidence_type || 'PHOTO')
      if (item.metadata.description) formData.append('description', item.metadata.description)

      await evidenceApi.upload(formData)
      success++
    } catch {
      failed++
    }
  }

  return { success, failed }
}

export function isOnline(): boolean {
  return navigator.onLine
}

export function onNetworkChange(
  onOnline: () => void,
  onOffline: () => void
): () => void {
  window.addEventListener('online', onOnline)
  window.addEventListener('offline', onOffline)
  return () => {
    window.removeEventListener('online', onOnline)
    window.removeEventListener('offline', onOffline)
  }
}
