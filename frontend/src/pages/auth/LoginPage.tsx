/**
 * Login page — clean government enterprise look.
 */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Activity, Lock, Mail, AlertCircle } from 'lucide-react'
import { useAuth } from '../../store/authStore'

const DEMO_CREDENTIALS = [
  { label: 'Department Official', email: 'official@aiip.gov.in', password: 'Demo@1234' },
  { label: 'PMU Officer', email: 'pmu@aiip.gov.in', password: 'Demo@1234' },
  { label: 'Inspector', email: 'insp1@aiip.gov.in', password: 'Demo@1234' },
]

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('official@aiip.gov.in')
  const [password, setPassword] = useState('Demo@1234')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/command-center', { replace: true })
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 via-navy-800 to-brand-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-teal-500 rounded-2xl mb-4">
            <Activity className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-white text-2xl font-bold">AIIP</h1>
          <p className="text-slate-400 text-sm mt-1">Adaptive Inspection Intelligence Platform</p>
          <p className="text-slate-500 text-xs mt-0.5">Ministry of Social Justice and Empowerment</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-xl shadow-xl p-6">
          <h2 className="text-slate-800 font-semibold text-lg mb-5">Sign in to continue</h2>

          {error && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-md px-3 py-2 mb-4 text-red-700 text-sm" role="alert">
              <AlertCircle className="w-4 h-4 flex-shrink-0" aria-hidden />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" aria-hidden />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="username"
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  placeholder="email@aiip.gov.in"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" aria-hidden />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full pl-9 pr-9 py-2.5 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-2.5"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          {/* Demo credentials */}
          <div className="mt-5 pt-4 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Demo credentials
            </p>
            <div className="space-y-1.5">
              {DEMO_CREDENTIALS.map((cred) => (
                <button
                  key={cred.email}
                  type="button"
                  onClick={() => { setEmail(cred.email); setPassword(cred.password) }}
                  className="w-full text-left px-3 py-2 text-xs rounded-md bg-slate-50 hover:bg-slate-100 transition-colors"
                >
                  <span className="font-medium text-slate-700">{cred.label}</span>
                  <span className="text-slate-500 ml-1">— {cred.email}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-slate-500 text-xs mt-4">
          SIH 2026 — PS 26095 — Prototype | Synthetic demo data only
        </p>
      </div>
    </div>
  )
}
