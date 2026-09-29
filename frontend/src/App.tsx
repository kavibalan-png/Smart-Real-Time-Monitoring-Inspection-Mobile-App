import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './store/AuthProvider'
import { useAuth } from './store/authStore'
import { AppShell } from './components/layout/AppShell'
import { LoginPage } from './pages/auth/LoginPage'
import { CommandCenter } from './pages/official/CommandCenter'
import { ProjectsList } from './pages/official/ProjectsList'
import { ProjectDetail } from './pages/official/ProjectDetail'
import { InspectionsList } from './pages/official/InspectionsList'
import { EvidenceReview } from './pages/official/EvidenceReview'
import { SurpriseAssignment } from './pages/official/SurpriseAssignment'
import { FollowupPage } from './pages/official/FollowupPage'
import { AuditPage } from './pages/official/AuditPage'
import { InspectorHome } from './pages/inspector/InspectorHome'
import { FieldInspection } from './pages/inspector/FieldInspection'
import { OfflineSync } from './pages/inspector/OfflineSync'
import { LoadingSpinner } from './components/shared/LoadingSpinner'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" label="Initializing..." />
      </div>
    )
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppRoutes() {
  const { user } = useAuth()
  const isInspector = user?.role === 'INSPECTION_OFFICER'

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        {/* Default redirect based on role */}
        <Route index element={
          <Navigate to={isInspector ? '/inspector/home' : '/command-center'} replace />
        } />

        {/* Official routes */}
        <Route path="command-center" element={<CommandCenter />} />
        <Route path="projects" element={<ProjectsList />} />
        <Route path="projects/:id" element={<ProjectDetail />} />
        <Route path="inspections" element={<InspectionsList />} />
        <Route path="inspections/:id/review" element={<EvidenceReview />} />
        <Route path="inspections/assign/:projectId" element={<SurpriseAssignment />} />
        <Route path="followups" element={<FollowupPage />} />
        <Route path="audit" element={<AuditPage />} />

        {/* Inspector routes */}
        <Route path="inspector/home" element={<InspectorHome />} />
        <Route path="inspector/inspection/:id" element={<FieldInspection />} />
        <Route path="inspector/sync" element={<OfflineSync />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
