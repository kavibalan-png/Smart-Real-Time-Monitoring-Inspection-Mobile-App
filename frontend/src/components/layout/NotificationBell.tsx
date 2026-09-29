import React, { useState, useRef, useEffect } from 'react'
import { Bell } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '../../services/api'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const qc = useQueryClient()

  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list({ per_page: 10 }).then((r) => r.data),
    refetchInterval: 30000,
  })

  const markAll = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const unreadCount = data?.unread_count || 0

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const priorityColor: Record<string, string> = {
    CRITICAL: 'bg-red-50 border-red-200',
    HIGH: 'bg-orange-50 border-orange-200',
    MEDIUM: 'bg-blue-50 border-blue-200',
    LOW: 'bg-slate-50 border-slate-200',
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
        aria-label={`Notifications${unreadCount > 0 ? ` — ${unreadCount} unread` : ''}`}
        aria-haspopup="true"
        aria-expanded={open}
      >
        <Bell className="w-5 h-5" aria-hidden />
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 w-4.5 h-4.5 min-w-[1.1rem] bg-red-600 text-white text-xs rounded-full flex items-center justify-center font-bold"
            aria-hidden
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          className="absolute right-0 top-11 w-80 bg-white rounded-lg border border-slate-200 shadow-lg z-50 overflow-hidden"
          role="dialog"
          aria-label="Notifications panel"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <h3 className="font-semibold text-slate-800 text-sm">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={() => markAll.mutate()}
                className="text-xs text-brand-600 hover:text-brand-800"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
            {(!data?.items || data.items.length === 0) ? (
              <div className="px-4 py-6 text-center text-sm text-slate-500">
                No notifications
              </div>
            ) : (
              data.items.map((notif: any) => (
                <div
                  key={notif.id}
                  className={clsx(
                    'px-4 py-3 border-l-2',
                    !notif.is_read ? priorityColor[notif.priority] || 'bg-blue-50 border-blue-200' : 'bg-white border-transparent'
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className={clsx('text-sm font-medium truncate', !notif.is_read ? 'text-slate-900' : 'text-slate-600')}>
                        {notif.title}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{notif.message}</p>
                    </div>
                    {!notif.is_read && (
                      <div className="w-2 h-2 bg-brand-600 rounded-full flex-shrink-0 mt-1" aria-label="Unread" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    {formatDistanceToNow(new Date(notif.created_at), { addSuffix: true })}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
