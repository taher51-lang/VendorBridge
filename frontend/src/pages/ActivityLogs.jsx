import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/analyticsApi'
import { History, Filter, FileText, ClipboardList, ShoppingCart, Receipt, CheckSquare, Users } from 'lucide-react'

const ENTITY_TYPES = ['all', 'rfq', 'quotation', 'purchase_order', 'invoice', 'approval_workflow', 'vendor']

const ENTITY_ICONS = {
  rfq: FileText,
  quotation: ClipboardList,
  purchase_order: ShoppingCart,
  invoice: Receipt,
  approval_workflow: CheckSquare,
  vendor: Users,
}

const ACTION_COLORS = {
  created: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  approved: 'bg-blue-100 text-blue-700 border-blue-200',
  rejected: 'bg-rose-100 text-rose-700 border-rose-200',
  submitted: 'bg-violet-100 text-violet-700 border-violet-200',
  selected: 'bg-cyan-100 text-cyan-700 border-cyan-200',
  cancelled: 'bg-zinc-100 text-zinc-600 border-zinc-200',
  updated: 'bg-amber-100 text-amber-700 border-amber-200',
  initiated: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  acknowledged: 'bg-blue-100 text-blue-700 border-blue-200',
  fulfilled: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  email_sent: 'bg-violet-100 text-violet-700 border-violet-200',
  marked_paid: 'bg-emerald-100 text-emerald-700 border-emerald-200',
}

function formatDate(dateStr) {
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now - d
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function ActivityLogs() {
  const [entityType, setEntityType] = useState('all')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['activity-logs', entityType, page],
    queryFn: () => {
      const params = { page, per_page: 20 }
      if (entityType !== 'all') params.entity_type = entityType
      return analyticsApi.getActivityLogs(params).then(r => r.data)
    },
  })

  const logs = data?.data || []
  const meta = data?.meta || {}

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2">
          <History size={22} className="text-violet-500" />
          Activity Logs
        </h1>
        <p className="text-zinc-500 text-sm mt-1">
          Complete audit trail of all procurement activities.
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-5 flex-wrap">
        <Filter size={14} className="text-zinc-400" />
        {ENTITY_TYPES.map(type => (
          <button
            key={type}
            onClick={() => { setEntityType(type); setPage(1) }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
              entityType === type
                ? 'bg-violet-100 text-violet-700 border border-violet-200'
                : 'bg-zinc-50 text-zinc-500 border border-zinc-200 hover:bg-zinc-100'
            }`}
          >
            {type === 'all' ? 'All' : type.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="flex items-center gap-3 animate-pulse">
                <div className="w-8 h-8 rounded-full bg-zinc-100" />
                <div className="flex-1">
                  <div className="h-4 bg-zinc-100 rounded w-3/4 mb-1" />
                  <div className="h-3 bg-zinc-50 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : logs.length === 0 ? (
          <div className="py-16 text-center">
            <History size={40} className="mx-auto text-zinc-300 mb-3" />
            <p className="text-zinc-500 text-sm">No activity logs found</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-50">
            {logs.map((log, i) => {
              const Icon = ENTITY_ICONS[log.entity_type] || FileText
              const actionColor = ACTION_COLORS[log.action] || ACTION_COLORS.created

              return (
                <div key={i} className="flex items-start gap-3 px-5 py-4 hover:bg-zinc-50/50 transition-colors">
                  <div className="mt-0.5 p-2 rounded-lg bg-zinc-100 text-zinc-500 shrink-0">
                    <Icon size={14} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${actionColor}`}>
                        {log.action}
                      </span>
                      <span className="text-sm text-zinc-700 font-medium capitalize">
                        {log.entity_type?.replace(/_/g, ' ')}
                      </span>
                      {log.entity_id && (
                        <code className="text-xs text-zinc-400 bg-zinc-50 px-1.5 py-0.5 rounded font-mono">
                          {log.entity_id.slice(0, 8)}…
                        </code>
                      )}
                    </div>
                    {log.actor_id && (
                      <p className="text-xs text-zinc-400 mt-0.5">
                        By user {log.actor_id.slice(0, 8)}…
                        {log.ip_address && <span className="ml-2">from {log.ip_address}</span>}
                      </p>
                    )}
                  </div>
                  <time className="text-xs text-zinc-400 whitespace-nowrap shrink-0 mt-0.5">
                    {formatDate(log.created_at)}
                  </time>
                </div>
              )
            })}
          </div>
        )}

        {/* Pagination */}
        {meta.total_pages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-zinc-100">
            <p className="text-xs text-zinc-500">
              Page {meta.page} of {meta.total_pages} · {meta.total} total
            </p>
            <div className="flex gap-1">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={!meta.has_prev}
                className="px-3 py-1.5 rounded text-xs font-medium border border-zinc-200 hover:bg-zinc-50 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={!meta.has_next}
                className="px-3 py-1.5 rounded text-xs font-medium border border-zinc-200 hover:bg-zinc-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
