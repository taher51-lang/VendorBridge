import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { poApi } from '../api/poApi'
import { ShoppingCart, Eye, Check, Truck, X, Search, Filter } from 'lucide-react'
import useAuthStore from '../store/authStore'

const STATUS_STYLES = {
  issued: 'bg-blue-100 text-blue-700',
  acknowledged: 'bg-amber-100 text-amber-700',
  fulfilled: 'bg-emerald-100 text-emerald-700',
  cancelled: 'bg-rose-100 text-rose-700',
}

const STATUS_TABS = ['all', 'issued', 'acknowledged', 'fulfilled', 'cancelled']

function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLES[status] || 'bg-zinc-100 text-zinc-600'}`}>
      {status}
    </span>
  )
}

export default function PurchaseOrders() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [search, setSearch] = useState('')
  const [selectedPO, setSelectedPO] = useState(null)
  const [page, setPage] = useState(1)

  const isVendor = user?.role === 'vendor'
  const isOfficer = ['procurement_officer', 'admin'].includes(user?.role)

  const { data, isLoading } = useQuery({
    queryKey: ['purchase-orders', activeTab, page],
    queryFn: () => {
      const params = { page, per_page: 15 }
      if (activeTab !== 'all') params.status = activeTab
      return poApi.getAll(params).then(r => r.data)
    },
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (id) => poApi.acknowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
      setSelectedPO(null)
    },
  })

  const fulfillMutation = useMutation({
    mutationFn: (id) => poApi.fulfill(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
      setSelectedPO(null)
    },
  })

  const cancelMutation = useMutation({
    mutationFn: (id) => poApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
      setSelectedPO(null)
    },
  })

  const pos = data?.data || []
  const meta = data?.meta || {}

  const filteredPOs = search
    ? pos.filter(po =>
      po.po_number?.toLowerCase().includes(search.toLowerCase()) ||
      po.vendor_name?.toLowerCase().includes(search.toLowerCase())
    )
    : pos

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2">
          <ShoppingCart size={22} className="text-violet-500" />
          Purchase Orders
        </h1>
        <p className="text-zinc-500 text-sm mt-1">
          {isVendor ? 'View and manage purchase orders assigned to you.' : 'Track and manage all purchase orders.'}
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between mb-4 gap-4 flex-wrap">
        <div className="flex gap-1 bg-zinc-100 rounded-lg p-1">
          {STATUS_TABS.map(tab => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); setPage(1) }}
              className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors ${activeTab === tab
                  ? 'bg-white text-zinc-900 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-700'
                }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
          <input
            type="text"
            placeholder="Search POs..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-400 w-64"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-zinc-50 rounded animate-pulse" />
            ))}
          </div>
        ) : filteredPOs.length === 0 ? (
          <div className="py-16 text-center">
            <ShoppingCart size={40} className="mx-auto text-zinc-300 mb-3" />
            <p className="text-zinc-500 text-sm">No purchase orders found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs text-zinc-500 border-b border-zinc-100 bg-zinc-50/50">
                <th className="px-5 py-3 font-medium">PO Number</th>
                {!isVendor && <th className="px-5 py-3 font-medium">Vendor</th>}
                <th className="px-5 py-3 font-medium">Total Amount</th>
                <th className="px-5 py-3 font-medium">Currency</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Issued</th>
                <th className="px-5 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredPOs.map(po => (
                <tr key={po.id} className="border-b border-zinc-50 hover:bg-zinc-50/50 transition-colors">
                  <td className="px-5 py-3.5 text-sm font-medium text-zinc-800">{po.po_number}</td>
                  {!isVendor && (
                    <td className="px-5 py-3.5 text-sm text-zinc-600">{po.vendor_name || '—'}</td>
                  )}
                  <td className="px-5 py-3.5 text-sm font-medium text-zinc-800">
                    ₹{Number(po.total_amount || 0).toLocaleString('en-IN')}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-zinc-500">{po.currency}</td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={po.status} />
                  </td>
                  <td className="px-5 py-3.5 text-sm text-zinc-500">
                    {po.created_at ? new Date(po.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => setSelectedPO(po)}
                        className="p-1.5 rounded-md hover:bg-zinc-100 text-zinc-500 hover:text-zinc-700 transition-colors"
                        title="View Details"
                      >
                        <Eye size={15} />
                      </button>
                      {isVendor && po.status === 'issued' && (
                        <button
                          onClick={() => acknowledgeMutation.mutate(po.id)}
                          className="p-1.5 rounded-md hover:bg-blue-50 text-blue-600 hover:text-blue-800 transition-colors"
                          title="Acknowledge"
                          disabled={acknowledgeMutation.isPending}
                        >
                          <Check size={15} />
                        </button>
                      )}
                      {isVendor && po.status === 'acknowledged' && (
                        <button
                          onClick={() => fulfillMutation.mutate(po.id)}
                          className="p-1.5 rounded-md hover:bg-emerald-50 text-emerald-600 hover:text-emerald-800 transition-colors"
                          title="Mark Fulfilled"
                          disabled={fulfillMutation.isPending}
                        >
                          <Truck size={15} />
                        </button>
                      )}
                      {isOfficer && ['issued', 'acknowledged'].includes(po.status) && (
                        <button
                          onClick={() => cancelMutation.mutate(po.id)}
                          className="p-1.5 rounded-md hover:bg-rose-50 text-rose-500 hover:text-rose-700 transition-colors"
                          title="Cancel PO"
                          disabled={cancelMutation.isPending}
                        >
                          <X size={15} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
                className="px-3 py-1.5 rounded text-xs font-medium border border-zinc-200 hover:bg-zinc-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={!meta.has_next}
                className="px-3 py-1.5 rounded text-xs font-medium border border-zinc-200 hover:bg-zinc-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedPO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setSelectedPO(null)}>
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-900">{selectedPO.po_number}</h2>
              <button onClick={() => setSelectedPO(null)} className="p-1 hover:bg-zinc-100 rounded-lg">
                <X size={18} className="text-zinc-400" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-zinc-500 mb-0.5">Status</p>
                  <StatusBadge status={selectedPO.status} />
                </div>
                <div>
                  <p className="text-zinc-500 mb-0.5">Currency</p>
                  <p className="font-medium text-zinc-800">{selectedPO.currency}</p>
                </div>
                <div>
                  <p className="text-zinc-500 mb-0.5">Vendor</p>
                  <p className="font-medium text-zinc-800">{selectedPO.vendor_name || '—'}</p>
                </div>
                <div>
                  <p className="text-zinc-500 mb-0.5">RFQ Ref</p>
                  <p className="font-medium text-zinc-800">{selectedPO.rfq_number || '—'}</p>
                </div>
              </div>
              <div className="border-t border-zinc-100 pt-4">
                <h3 className="text-sm font-semibold text-zinc-900 mb-2">Financial Summary</h3>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div className="bg-zinc-50 rounded-lg p-3 text-center">
                    <p className="text-zinc-500 text-xs">Subtotal</p>
                    <p className="font-semibold text-zinc-800">₹{Number(selectedPO.subtotal || 0).toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-zinc-50 rounded-lg p-3 text-center">
                    <p className="text-zinc-500 text-xs">Tax</p>
                    <p className="font-semibold text-zinc-800">₹{Number(selectedPO.tax_amount || 0).toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-violet-50 rounded-lg p-3 text-center">
                    <p className="text-violet-500 text-xs">Total</p>
                    <p className="font-bold text-violet-800">₹{Number(selectedPO.total_amount || 0).toLocaleString('en-IN')}</p>
                  </div>
                </div>
              </div>
              {selectedPO.items?.length > 0 && (
                <div className="border-t border-zinc-100 pt-4">
                  <h3 className="text-sm font-semibold text-zinc-900 mb-2">Line Items</h3>
                  <div className="space-y-2">
                    {selectedPO.items.map((item, i) => (
                      <div key={i} className="flex items-center justify-between text-sm bg-zinc-50 rounded-lg px-3 py-2">
                        <div>
                          <p className="font-medium text-zinc-800">{item.item_name}</p>
                          <p className="text-xs text-zinc-500">Qty: {item.quantity} × ₹{item.unit_price}</p>
                        </div>
                        <p className="font-medium text-zinc-800">₹{Number(item.line_total || 0).toLocaleString('en-IN')}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedPO.delivery_address && (
                <div className="border-t border-zinc-100 pt-4">
                  <p className="text-zinc-500 text-sm mb-0.5">Delivery Address</p>
                  <p className="text-sm text-zinc-800">{selectedPO.delivery_address}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
