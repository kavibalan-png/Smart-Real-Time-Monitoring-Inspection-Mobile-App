/**
 * WebSocket hook — real-time command center updates.
 * Connects with JWT token, handles reconnection, broadcasts to query cache.
 */
import { useEffect, useRef, useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { tokenStorage } from '../services/api'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export type WSEvent = {
  type: string
  data: Record<string, any>
}

export function useWebSocket(enabled: boolean = true) {
  const qc = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [connected, setConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null)

  const connect = useCallback(() => {
    const token = tokenStorage.get()
    if (!token || !enabled) return

    try {
      const ws = new WebSocket(`${WS_URL}/api/ws?token=${token}`)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        // Keepalive ping every 25s
        const ping = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping')
        }, 25000)
        ws.onclose = () => {
          clearInterval(ping)
          setConnected(false)
          // Reconnect after 5s
          reconnectTimeout.current = setTimeout(connect, 5000)
        }
      }

      ws.onmessage = (evt) => {
        try {
          const event: WSEvent = JSON.parse(evt.data)
          if (event.type === 'pong' || event.type === 'CONNECTED') return
          setLastEvent(event)
          handleEvent(event)
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      // WebSocket not available — fall back to polling
      reconnectTimeout.current = setTimeout(connect, 10000)
    }
  }, [enabled, qc])

  function handleEvent(event: WSEvent) {
    // Invalidate relevant queries based on event type
    switch (event.type) {
      case 'ANOMALY_DETECTED':
      case 'ALERT_CREATED':
        qc.invalidateQueries({ queryKey: ['monitoring-summary'] })
        qc.invalidateQueries({ queryKey: ['alerts'] })
        if (event.data?.project_id) {
          qc.invalidateQueries({ queryKey: ['anomalies', event.data.project_id] })
          qc.invalidateQueries({ queryKey: ['project', event.data.project_id] })
        }
        break

      case 'INSPECTION_ASSIGNED':
      case 'INSPECTION_STARTED':
      case 'INSPECTION_SUBMITTED':
        qc.invalidateQueries({ queryKey: ['inspections-all'] })
        qc.invalidateQueries({ queryKey: ['my-inspections'] })
        qc.invalidateQueries({ queryKey: ['monitoring-summary'] })
        break

      case 'EVIDENCE_UPLOADED':
        if (event.data?.inspection_id) {
          qc.invalidateQueries({ queryKey: ['inspection', event.data.inspection_id] })
          qc.invalidateQueries({ queryKey: ['timeline', event.data.inspection_id] })
        }
        break

      case 'CAMERA_OFFLINE':
      case 'CAMERA_ONLINE':
        qc.invalidateQueries({ queryKey: ['cameras'] })
        qc.invalidateQueries({ queryKey: ['monitoring-summary'] })
        break

      case 'DECISION_MADE':
      case 'FOLLOWUP_CREATED':
        qc.invalidateQueries({ queryKey: ['followups'] })
        qc.invalidateQueries({ queryKey: ['monitoring-summary'] })
        break

      case 'NOTIFICATION':
        qc.invalidateQueries({ queryKey: ['notifications'] })
        break
    }
  }

  useEffect(() => {
    if (enabled) connect()
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current)
      wsRef.current?.close()
    }
  }, [connect, enabled])

  return { connected, lastEvent }
}
