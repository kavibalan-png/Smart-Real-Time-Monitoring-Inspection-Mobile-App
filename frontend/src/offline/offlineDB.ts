/**
 * IndexedDB offline storage for field inspection operations.
 * Ensures zero data loss when network is unavailable.
 */
import { openDB, DBSchema, IDBPDatabase } from 'idb'
import type { OfflineOperation } from '../types'

interface AIIPOfflineDB extends DBSchema {
  operations: {
    key: string
    value: OfflineOperation
    indexes: { by_status: string; by_type: string }
  }
  evidence_queue: {
    key: string
    value: {
      local_id: string
      inspection_id: number
      file_data: Blob
      metadata: Record<string, any>
      created_at: string
      sync_status: string
    }
    indexes: { by_inspection: number }
  }
  inspection_cache: {
    key: number
    value: Record<string, any>
  }
}

let db: IDBPDatabase<AIIPOfflineDB> | null = null

export async function getDB(): Promise<IDBPDatabase<AIIPOfflineDB>> {
  if (db) return db
  db = await openDB<AIIPOfflineDB>('aiip-offline-v1', 1, {
    upgrade(database) {
      // Operations queue
      const opStore = database.createObjectStore('operations', { keyPath: 'local_id' })
      opStore.createIndex('by_status', 'sync_status')
      opStore.createIndex('by_type', 'operation_type')

      // Evidence files queue
      const evStore = database.createObjectStore('evidence_queue', { keyPath: 'local_id' })
      evStore.createIndex('by_inspection', 'inspection_id')

      // Inspection data cache
      database.createObjectStore('inspection_cache', { keyPath: 'id' })
    },
  })
  return db
}

export async function queueOperation(
  operationType: string,
  payload: Record<string, any>
): Promise<string> {
  const database = await getDB()
  const local_id = `local_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
  const operation: OfflineOperation = {
    local_id,
    operation_type: operationType,
    payload,
    created_at: new Date().toISOString(),
    sync_status: 'PENDING',
    retry_count: 0,
  }
  await database.put('operations', operation)
  return local_id
}

export async function getPendingOperations(): Promise<OfflineOperation[]> {
  const database = await getDB()
  const all = await database.getAll('operations')
  return all.filter((op) =>
    ['PENDING', 'FAILED', 'RETRY'].includes(op.sync_status)
  )
}

export async function updateOperationStatus(
  local_id: string,
  status: OfflineOperation['sync_status']
): Promise<void> {
  const database = await getDB()
  const op = await database.get('operations', local_id)
  if (op) {
    op.sync_status = status
    if (status === 'RETRY') op.retry_count += 1
    await database.put('operations', op)
  }
}

export async function queueEvidenceFile(
  inspectionId: number,
  file: Blob,
  metadata: Record<string, any>
): Promise<string> {
  const database = await getDB()
  const local_id = `evd_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
  await database.put('evidence_queue', {
    local_id,
    inspection_id: inspectionId,
    file_data: file,
    metadata,
    created_at: new Date().toISOString(),
    sync_status: 'PENDING',
  })
  return local_id
}

export async function getPendingEvidenceFiles(inspectionId: number) {
  const database = await getDB()
  const index = database.transaction('evidence_queue').store.index('by_inspection')
  return index.getAll(inspectionId)
}

export async function cacheInspection(inspection: Record<string, any>): Promise<void> {
  const database = await getDB()
  await database.put('inspection_cache', inspection)
}

export async function getCachedInspection(id: number): Promise<Record<string, any> | undefined> {
  const database = await getDB()
  return database.get('inspection_cache', id)
}

export async function getPendingCount(): Promise<number> {
  const pending = await getPendingOperations()
  return pending.length
}
