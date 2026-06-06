import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../../api/analyticsApi'
import { FileText, ClipboardList, CheckSquare, Receipt, ShoppingCart, Clock, Plus, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'

function StatCard({ icon: Icon, label, value, color = 'violet', sub, onClick }) {
  const colors = {
    violet: 'bg-violet-50 text-violet-600',
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    cyan: 'bg-cyan-50 text-cyan-600',
    indigo: 'bg-indigo-50 text-indigo-600',
  }

  return (
    <div
      className={`bg-white rounded-xl border border-zinc-200 p-5 hover:shadow-md transition-shadow duration-200 ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
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

function QuickAction({ icon: Icon, label, onClick, color = 'violet' }) {
  const bg = {
    violet: 'bg-violet-600 hover:bg-violet-700',
    blue: 'bg-blue-600 hover:bg-blue-700',
    emerald: 'bg-emerald-600 hover:bg-emerald-700',
  }

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-white ${bg[color]} transition-colors`}
    >
      <Icon size={15} />
      {label}
    </button>
  )
}

export default function OfficerDashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => analyticsApi.getDashboard().then(r => r.data?.data),
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">Procurement Dashboard</h1>
          <p className="text-zinc-500 text-sm mt-1">
            Welcome back, {user?.full_name}. Here's what's happening.
          </p>
        </div>
        <div className="flex gap-2">
          <QuickAction icon={Plus} label="New RFQ" onClick={() => navigate('/rfqs')} color="violet" />
          <QuickAction icon={ClipboardList} label="Quotations" onClick={() => navigate('/quotations')} color="blue" />
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-zinc-200 p-5 animate-pulse">
              <div className="h-4 bg-zinc-100 rounded w-24 mb-2" />
              <div className="h-7 bg-zinc-100 rounded w-16" />
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <StatCard icon={FileText} label="Active RFQs" value={data?.active_rfqs} color="violet" onClick={() => navigate('/rfqs')} />
            <StatCard icon={ClipboardList} label="Quotations Received" value={data?.quotations_received} color="blue" onClick={() => navigate('/quotations')} />
            <StatCard icon={CheckSquare} label="Pending Approvals" value={data?.pending_approvals} color="amber" onClick={() => navigate('/approvals')} />
            <StatCard icon={ShoppingCart} label="Total POs" value={data?.total_pos} color="cyan" onClick={() => navigate('/purchase-orders')} />
            <StatCard icon={Receipt} label="Invoices This Month" value={data?.invoices_this_month} color="indigo" onClick={() => navigate('/invoices')} />
          </div>

          {/* Recent RFQs */}
          <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-zinc-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-zinc-900 flex items-center gap-2">
                <Clock size={15} className="text-zinc-400" />
                Recent RFQs
              </h2>
              <button onClick={() => navigate('/rfqs')} className="text-xs text-violet-600 hover:text-violet-800 flex items-center gap-1">
                View All <ArrowRight size={12} />
              </button>
            </div>
            {data?.recent_rfqs?.length > 0 ? (
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs text-zinc-500 border-b border-zinc-100">
                    <th className="px-5 py-2.5 font-medium">RFQ Number</th>
                    <th className="px-5 py-2.5 font-medium">Title</th>
                    <th className="px-5 py-2.5 font-medium">Status</th>
                    <th className="px-5 py-2.5 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_rfqs.map((rfq) => (
                    <tr key={rfq.id} className="border-b border-zinc-50 hover:bg-zinc-50/50 transition-colors">
                      <td className="px-5 py-3 text-sm font-medium text-zinc-800">{rfq.rfq_number}</td>
                      <td className="px-5 py-3 text-sm text-zinc-600 max-w-xs truncate">{rfq.title}</td>
                      <td className="px-5 py-3">
                        <StatusBadge status={rfq.status} />
                      </td>
                      <td className="px-5 py-3 text-sm text-zinc-500">
                        {new Date(rfq.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-zinc-400 py-8 text-center">No RFQs created yet</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function StatusBadge({ status }) {
  const styles = {
    draft: 'bg-zinc-100 text-zinc-600',
    open: 'bg-emerald-100 text-emerald-700',
    under_review: 'bg-amber-100 text-amber-700',
    awarded: 'bg-blue-100 text-blue-700',
    closed: 'bg-zinc-100 text-zinc-600',
    cancelled: 'bg-rose-100 text-rose-700',
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[status] || styles.draft}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  )
}
