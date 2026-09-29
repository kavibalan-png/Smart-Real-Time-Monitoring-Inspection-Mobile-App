/**
 * Main application shell — sidebar nav + content area.
 * Role-aware navigation items.
 */
import React, { useState } from 'react'
import { NavLink, useNavigate, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Map, Search, Shield, FileCheck, Bell,
  ClipboardList, LogOut, Menu, X, Activity, Users, ChevronRight,
  Wifi, WifiOff
} from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../../store/authStore'
import { NotificationBell } from './NotificationBell'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import { useWebSocket } from '../../hooks/useWebSocket'

interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
  roles: string[]
  badge?: number
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/command-center',
    label: 'Command Center',
    icon: <LayoutDashboard className="w-5 h-5" />,
    roles: ['SUPER_ADMIN', 'DEPARTMENT_OFFICIAL', 'PMU_OFFICER'],
  },
  {
    to: '/projects',
    label: 'Projects',
    icon: <Map className="w-5 h-5" />,
    roles: ['SUPER_ADMIN', 'DEPARTMENT_OFFICIAL', 'PMU_OFFICER'],
  },
  {
    to: '/inspections',
    label: 'Inspections',
    icon: <Search className="w-5 h-5" />,
    roles: ['SUPER_ADMIN', 'DEPARTMENT_OFFICIAL', 'PMU_OFFICER'],
  },
  {
    to: '/inspector/home',
    label: 'My Inspections',
    icon: <ClipboardList className="w-5 h-5" />,
    roles: ['INSPECTION_OFFICER'],
  },
  {
    to: '/followups',
    label: 'Follow-up',
    icon: <FileCheck className="w-5 h-5" />,
    roles: ['SUPER_ADMIN', 'DEPARTMENT_OFFICIAL', 'PMU_OFFICER'],
  },
  {
    to: '/audit',
    label: 'Audit Trail',
    icon: <Shield className="w-5 h-5" />,
    roles: ['SUPER_ADMIN', 'DEPARTMENT_OFFICIAL', 'PMU_OFFICER'],
  },
]

export function AppShell() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const isOnline = useOnlineStatus()
  const { connected: wsConnected } = useWebSocket(!!user)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const visibleItems = NAV_ITEMS.filter(
    (item) => user && item.roles.includes(user.role)
  )

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const roleLabel: Record<string, string> = {
    SUPER_ADMIN: 'Super Admin',
    DEPARTMENT_OFFICIAL: 'Dept. Official',
    PMU_OFFICER: 'PMU Officer',
    INSPECTION_OFFICER: 'Inspector',
    PROJECT_ADMIN: 'Project Admin',
    PROJECT_STAFF: 'Project Staff',
    CITIZEN: 'Citizen',
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed lg:static inset-y-0 left-0 z-30 w-64 bg-navy-900 flex flex-col transition-transform duration-200',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
        aria-label="Main navigation"
      >
        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center flex-shrink-0">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="text-white font-bold text-sm leading-tight">AIIP</div>
              <div className="text-slate-400 text-xs">Inspection Intelligence</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-3" aria-label="Navigation">
          <div className="space-y-0.5">
            {visibleItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-teal-600 text-white'
                      : 'text-slate-300 hover:bg-white/10 hover:text-white'
                  )
                }
                aria-current={({ isActive }: { isActive: boolean }) => isActive ? 'page' : undefined}
              >
                <span aria-hidden>{item.icon}</span>
                <span className="flex-1">{item.label}</span>
                <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100" aria-hidden />
              </NavLink>
            ))}
          </div>
        </nav>

        {/* User section */}
        <div className="border-t border-white/10 px-4 py-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-brand-600 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-sm font-medium truncate">{user?.full_name}</div>
              <div className="text-slate-400 text-xs">{roleLabel[user?.role || '']}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/10 rounded-md transition-colors"
            aria-label="Log out"
          >
            <LogOut className="w-4 h-4" aria-hidden />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-4 flex-shrink-0">
          <button
            className="lg:hidden p-1.5 rounded-md hover:bg-slate-100"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5 text-slate-600" aria-hidden />
          </button>

          <div className="flex-1" />

          {/* Online + WS status */}
          <div className={clsx(
            'flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full',
            isOnline
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-red-50 text-red-700'
          )}>
            {isOnline ? (
              <><Wifi className="w-3 h-3" aria-hidden /><span>Online</span></>
            ) : (
              <><WifiOff className="w-3 h-3" aria-hidden /><span>Offline</span></>
            )}
          </div>
          {wsConnected && (
            <div className="hidden md:flex items-center gap-1 text-xs text-teal-700 font-medium">
              <span className="w-1.5 h-1.5 bg-teal-500 rounded-full animate-pulse" aria-hidden />
              Live
            </div>
          )}

          {/* Notifications */}
          <NotificationBell />

          <div className="text-xs text-slate-500 hidden md:block">
            Ministry of Social Justice & Empowerment
          </div>
        </header>

        {/* Page content */}
        <main
          className="flex-1 overflow-y-auto"
          id="main-content"
          tabIndex={-1}
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
