import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { vendorApi } from '../api/vendorApi'
import useAuthStore from '../store/authStore'

const STATUS_COLORS = {
  active: 'bg-emerald-100 text-emerald-700',
  pending: 'bg-amber-100 text-amber-700',
  suspended: 'bg-red-100 text-red-700',
  blacklisted: 'bg-zinc-100 text-zinc-500',
}

const TABS = ['all', 'active', 'pending', 'suspended', 'blacklisted']

export default function Vendors() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'
  const [activeTab, setActiveTab] = useState('all')
  const [search, setSearch] = useState('')
  const [actionModal, setActionModal] = useState(null)
  const [reason, setReason] = useState('')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['vendors', activeTab, search],
    queryFn: () => vendorApi.getAll({
      status: activeTab === 'all' ? undefined : activeTab,
      search: search || undefined,
      per_page: 50,
    }).then(r => r.data),
  })

  const vendors = data?.data || []

  const approveMutation = useMutation({
    mutationFn: (id) => vendorApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['vendors'])
      setActionModal(null)
    },
  })

  const suspendMutation = useMutation({
    mutationFn: ({ id, reason }) => vendorApi.suspend(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries(['vendors'])
      setActionModal(null)
      setReason('')
    },
  })

  const blacklistMutation = useMutation({
    mutationFn: ({ id, reason }) => vendorApi.blacklist(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries(['vendors'])
      setActionModal(null)
      setReason('')
    },
  })

  const handleAction = () => {
    if (actionModal.type === 'approve') approveMutation.mutate(actionModal.vendor.id)
    if (actionModal.type === 'suspend') suspendMutation.mutate({ id: actionModal.vendor.id, reason })
    if (actionModal.type === 'blacklist') blacklistMutation.mutate({ id: actionModal.vendor.id, reason })
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">Vendors</h1>
          <p className="text-zinc-500 text-sm mt-1">Manage supplier profiles and registrations</p>
        </div>
      </div>

      {/* Search + Tabs */}
      <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        <div className="px-5 pt-4 pb-0 border-b border-zinc-100">
          <div className="flex items-center gap-4 mb-4">
            <input
              type="text"
              placeholder="Search by name, GST, city..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-72 border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
            />
          </div>
          <div className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-zinc-900 text-zinc-900'
                    : 'border-transparent text-zinc-500 hover:text-zinc-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="py-16 text-center text-zinc-400 text-sm">Loading vendors...</div>
        ) : vendors.length === 0 ? (
          <div className="py-16 text-center text-zinc-400 text-sm">No vendors found.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-zinc-50 border-b border-zinc-100">
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Company</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">GST</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">City</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Rating</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Status</th>
                {isAdmin && <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {vendors.map((vendor) => (
                <tr key={vendor.id} className="border-b border-zinc-100 last:border-0 hover:bg-zinc-50">
                  <td className="px-5 py-3.5">
                    <p className="font-medium text-zinc-900">{vendor.company_name}</p>
                    <p className="text-zinc-400 text-xs">{vendor.state}</p>
                  </td>
                  <td className="px-5 py-3.5 text-zinc-500 font-mono text-xs">{vendor.gst_number || '—'}</td>
                  <td className="px-5 py-3.5 text-zinc-500">{vendor.city || '—'}</td>
                  <td className="px-5 py-3.5">
                    {vendor.avg_rating > 0 ? (
                      <span className="text-amber-600 font-medium">★ {parseFloat(vendor.avg_rating).toFixed(1)}</span>
                    ) : (
                      <span className="text-zinc-300">—</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[vendor.status]}`}>
                      {vendor.status}
                    </span>
                  </td>
                  {isAdmin && (
                    <td className="px-5 py-3.5">
                      <div className="flex gap-2">
                        {vendor.status === 'pending' && (
                          <button
                            onClick={() => setActionModal({ type: 'approve', vendor })}
                            className="text-xs text-emerald-600 hover:underline"
                          >
                            Approve
                          </button>
                        )}
                        {vendor.status === 'active' && (
                          <button
                            onClick={() => setActionModal({ type: 'suspend', vendor })}
                            className="text-xs text-amber-600 hover:underline"
                          >
                            Suspend
                          </button>
                        )}
                        {vendor.status !== 'blacklisted' && (
                          <button
                            onClick={() => setActionModal({ type: 'blacklist', vendor })}
                            className="text-xs text-red-500 hover:underline"
                          >
                            Blacklist
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Action Modal */}
      {actionModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100">
              <h2 className="text-lg font-semibold text-zinc-900 capitalize">
                {actionModal.type} vendor
              </h2>
              <button onClick={() => { setActionModal(null); setReason('') }} className="text-zinc-400 hover:text-zinc-600 text-xl">×</button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <p className="text-sm text-zinc-600">
                Are you sure you want to <strong>{actionModal.type}</strong> <strong>{actionModal.vendor.company_name}</strong>?
              </p>
              {(actionModal.type === 'suspend' || actionModal.type === 'blacklist') && (
                <div>
                  <label className="text-sm font-medium text-zinc-700 block mb-1.5">Reason</label>
                  <textarea
                    rows={3}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Provide a reason..."
                    className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 resize-none"
                  />
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => { setActionModal(null); setReason('') }}
                  className="flex-1 border border-zinc-200 text-zinc-700 text-sm px-4 py-2 rounded-lg hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAction}
                  disabled={approveMutation.isPending || suspendMutation.isPending || blacklistMutation.isPending}
                  className={`flex-1 text-white text-sm px-4 py-2 rounded-lg transition-colors disabled:opacity-50 ${
                    actionModal.type === 'approve' ? 'bg-emerald-600 hover:bg-emerald-700' :
                    actionModal.type === 'suspend' ? 'bg-amber-600 hover:bg-amber-700' :
                    'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
