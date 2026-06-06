import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../../api/analyticsApi'
import { Users, Building2, FileText, ShoppingCart, Receipt, CheckSquare, Clock, TrendingUp } from 'lucide-react'
import useAuthStore from '../../store/authStore'

function StatCard({ icon: Icon, label, value, color = 'violet', sub }) {
  const colors = {
    violet: 'bg-violet-50 text-violet-600',
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    rose: 'bg-rose-50 text-rose-600',
    cyan: 'bg-cyan-50 text-cyan-600',
    indigo: 'bg-indigo-50 text-indigo-600',
    orange: 'bg-orange-50 text-orange-600',
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

function ActivityItem({ log }) {
  const actionColors = {
    created: 'bg-emerald-100 text-emerald-700',
    approved: 'bg-blue-100 text-blue-700',
    rejected: 'bg-rose-100 text-rose-700',
    submitted: 'bg-violet-100 text-violet-700',
    cancelled: 'bg-zinc-100 text-zinc-700',
    default: 'bg-zinc-100 text-zinc-600',
  }

  const color = actionColors[log.action] || actionColors.default

  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-zinc-100 last:border-0">
      <div className={`px-2 py-0.5 rounded text-xs font-medium ${color}`}>
        {log.action}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-zinc-700 truncate">
          <span className="font-medium">{log.entity_type}</span>
          {log.entity_id && <span className="text-zinc-400 ml-1">#{log.entity_id?.slice(0, 8)}</span>}
        </p>
      </div>
      <time className="text-xs text-zinc-400 whitespace-nowrap">
        {new Date(log.created_at).toLocaleDateString()}
      </time>
    </div>
  )
}

export default function AdminDashboard() {
  const { user } = useAuthStore()
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => analyticsApi.getDashboard().then(r => r.data?.data),
  })

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900">Admin Dashboard</h1>
        <p className="text-zinc-500 text-sm mt-1">
          Welcome back, {user?.full_name}. System overview at a glance.
        </p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-zinc-200 p-5 animate-pulse">
              <div className="h-4 bg-zinc-100 rounded w-24 mb-2" />
              <div className="h-7 bg-zinc-100 rounded w-16" />
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard icon={Users} label="Total Users" value={data?.total_users} color="violet" />
            <StatCard icon={Building2} label="Total Vendors" value={data?.total_vendors} color="blue" sub={`${data?.active_vendors || 0} active · ${data?.pending_vendors || 0} pending`} />
            <StatCard icon={FileText} label="Active RFQs" value={data?.active_rfqs} color="emerald" />
            <StatCard icon={CheckSquare} label="Pending Approvals" value={data?.pending_approvals} color="amber" />
            <StatCard icon={ShoppingCart} label="Total POs" value={data?.total_pos} color="cyan" />
            <StatCard icon={Receipt} label="Total Invoices" value={data?.total_invoices} color="indigo" />
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-xl border border-zinc-200 p-5">
            <h2 className="text-sm font-semibold text-zinc-900 mb-3 flex items-center gap-2">
              <Clock size={15} className="text-zinc-400" />
              Recent Activity
            </h2>
            {data?.recent_activity?.length > 0 ? (
              <div className="divide-y-0">
                {data.recent_activity.map((log, i) => (
                  <ActivityItem key={i} log={log} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-zinc-400 py-4 text-center">No recent activity</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
