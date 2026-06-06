import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../../api/analyticsApi'
import { CheckSquare, ThumbsUp, ThumbsDown, LayoutList, Clock } from 'lucide-react'
import useAuthStore from '../../store/authStore'
import { useNavigate } from 'react-router-dom'

function StatCard({ icon: Icon, label, value, color = 'violet', sub }) {
  const colors = {
    violet: 'bg-violet-50 text-violet-600',
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    rose: 'bg-rose-50 text-rose-600',
  }

  return (
    <div className="bg-white rounded-xl border border-zinc-200 p-5 hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-zinc-500 mb-1">{label}</p>
          <p className="text-2xl font-bold text-zinc-900">{value ?? '—'}</p>
          {sub && <p className="text-xs text-zinc-400 mt-1">{sub}</p>}
        </div>
        <div className={`p-2.5 rounded-lg ${colors[color]}`}>
          <Icon size={18} />
        </div>
      </div>
    </div>
  )
}

export default function ManagerDashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => analyticsApi.getDashboard().then(r => r.data?.data),
  })

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900">Manager Dashboard</h1>
        <p className="text-zinc-500 text-sm mt-1">
          Welcome back, {user?.full_name}. Review pending approvals below.
        </p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-zinc-200 p-5 animate-pulse">
              <div className="h-4 bg-zinc-100 rounded w-24 mb-2" />
              <div className="h-7 bg-zinc-100 rounded w-16" />
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              icon={CheckSquare}
              label="Pending Approvals"
              value={data?.pending_approvals}
              color="amber"
              sub="Waiting for your action"
            />
            <StatCard
              icon={ThumbsUp}
              label="Approved This Month"
              value={data?.approved_this_month}
              color="emerald"
            />
            <StatCard
              icon={ThumbsDown}
              label="Rejected"
              value={data?.rejected}
              color="rose"
            />
            <StatCard
              icon={LayoutList}
              label="Total Workflows"
              value={data?.total_workflows}
              color="blue"
            />
          </div>

          {/* Pending Approvals CTA */}
          {(data?.pending_approvals || 0) > 0 && (
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-200 p-6 mb-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-amber-100 rounded-full">
                    <Clock size={20} className="text-amber-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-zinc-900">
                      {data.pending_approvals} approval{data.pending_approvals !== 1 ? 's' : ''} waiting
                    </h3>
                    <p className="text-sm text-zinc-500">Review and approve or reject pending workflows</p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/approvals')}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  Review Now
                </button>
              </div>
            </div>
          )}

          {/* Summary Section */}
          <div className="bg-white rounded-xl border border-zinc-200 p-5">
            <h2 className="text-sm font-semibold text-zinc-900 mb-4">Approval Overview</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-600">Approval Rate</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-zinc-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                      style={{
                        width: `${data?.total_workflows
                          ? Math.round(((data?.approved_this_month || 0) / Math.max(data.total_workflows, 1)) * 100)
                          : 0}%`
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium text-zinc-800">
                    {data?.total_workflows
                      ? Math.round(((data?.approved_this_month || 0) / Math.max(data.total_workflows, 1)) * 100)
                      : 0}%
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-600">Rejection Rate</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-zinc-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-rose-500 rounded-full transition-all duration-500"
                      style={{
                        width: `${data?.total_workflows
                          ? Math.round(((data?.rejected || 0) / Math.max(data.total_workflows, 1)) * 100)
                          : 0}%`
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium text-zinc-800">
                    {data?.total_workflows
                      ? Math.round(((data?.rejected || 0) / Math.max(data.total_workflows, 1)) * 100)
                      : 0}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
