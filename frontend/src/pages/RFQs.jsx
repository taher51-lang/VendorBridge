import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useFieldArray } from 'react-hook-form'
import { rfqApi } from '../api/rfqApi'
import { vendorApi } from '../api/vendorApi'
import useAuthStore from '../store/authStore'

const STATUS_COLORS = {
  draft: 'bg-zinc-100 text-zinc-600',
  open: 'bg-blue-100 text-blue-700',
  under_review: 'bg-amber-100 text-amber-700',
  awarded: 'bg-violet-100 text-violet-700',
  closed: 'bg-emerald-100 text-emerald-700',
  cancelled: 'bg-red-100 text-red-700',
}

const TABS = ['all', 'draft', 'open', 'under_review', 'awarded', 'closed']

export default function RFQs() {
  const { user } = useAuthStore()
  const isOfficer = user?.role === 'procurement_officer' || user?.role === 'admin'
  const isVendor = user?.role === 'vendor'
  const [activeTab, setActiveTab] = useState('all')
  const [showModal, setShowModal] = useState(false)
  const [selectedRFQ, setSelectedRFQ] = useState(null)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['rfqs', activeTab],
    queryFn: () => rfqApi.getAll({
      status: activeTab === 'all' ? undefined : activeTab,
      per_page: 50,
    }).then(r => r.data),
  })

  const { data: vendorsData } = useQuery({
    queryKey: ['vendors-active'],
    queryFn: () => vendorApi.getAll({ status: 'active', per_page: 100 }).then(r => r.data),
    enabled: isOfficer,
  })

  const rfqs = data?.data || []
  const vendors = vendorsData?.data || []

  const { register, control, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: {
      items: [{ item_name: '', quantity: 1, unit: 'pcs', description: '' }]
    }
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'items' })

  const createMutation = useMutation({
    mutationFn: (data) => rfqApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['rfqs'])
      setShowModal(false)
      reset()
    },
  })

  const publishMutation = useMutation({
    mutationFn: (id) => rfqApi.publish(id),
    onSuccess: () => queryClient.invalidateQueries(['rfqs']),
  })

  const cancelMutation = useMutation({
    mutationFn: (id) => rfqApi.cancel(id),
    onSuccess: () => queryClient.invalidateQueries(['rfqs']),
  })

  const onSubmit = (data) => {
    const payload = {
      ...data,
      deadline: new Date(data.deadline).toISOString(),
      vendor_ids: data.vendor_ids || [],
    }
    createMutation.mutate(payload)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">RFQs</h1>
          <p className="text-zinc-500 text-sm mt-1">
            {isVendor ? 'RFQs you have been invited to' : 'Manage request for quotations'}
          </p>
        </div>
        {isOfficer && (
          <button
            onClick={() => setShowModal(true)}
            className="bg-zinc-900 hover:bg-zinc-800 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            + Create RFQ
          </button>
        )}
      </div>

      {/* Tabs */}
      {isOfficer && (
        <div className="flex gap-1 mb-4 border-b border-zinc-200">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${activeTab === tab
                ? 'border-zinc-900 text-zinc-900'
                : 'border-transparent text-zinc-500 hover:text-zinc-700'
                }`}
            >
              {tab.replace('_', ' ')}
            </button>
          ))}
        </div>
      )}

      {/* RFQ Cards */}
      {isLoading ? (
        <div className="bg-white rounded-xl border border-zinc-200 py-16 text-center text-zinc-400 text-sm">Loading...</div>
      ) : rfqs.length === 0 ? (
        <div className="bg-white rounded-xl border border-zinc-200 py-16 text-center text-zinc-400 text-sm">
          No RFQs found.
        </div>
      ) : (
        <div className="space-y-3">
          {rfqs.map((rfq) => (
            <div
              key={rfq.id}
              className="bg-white rounded-xl border border-zinc-200 p-5 hover:border-zinc-300 transition-colors cursor-pointer"
              onClick={() => setSelectedRFQ(rfq)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-zinc-400">{rfq.rfq_number}</span>
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[rfq.status]}`}>
                      {rfq.status?.replace('_', ' ')}
                    </span>
                  </div>
                  <h3 className="font-medium text-zinc-900">{rfq.title}</h3>
                  {rfq.description && (
                    <p className="text-zinc-500 text-sm mt-1 truncate">{rfq.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-zinc-400">
                    <span>{rfq.items?.length || 0} item{rfq.items?.length !== 1 ? 's' : ''}</span>
                    <span>Deadline: {rfq.deadline ? new Date(rfq.deadline).toLocaleDateString() : '—'}</span>
                    <span>{rfq.vendor_assignments?.length || 0} vendor{rfq.vendor_assignments?.length !== 1 ? 's' : ''} invited</span>
                  </div>
                </div>
                {isOfficer && (
                  <div className="flex gap-2 ml-4" onClick={(e) => e.stopPropagation()}>
                    {rfq.status === 'draft' && (
                      <button
                        onClick={() => publishMutation.mutate(rfq.id)}
                        className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg transition-colors"
                      >
                        Publish
                      </button>
                    )}
                    {(rfq.status === 'draft' || rfq.status === 'open') && (
                      <button
                        onClick={() => cancelMutation.mutate(rfq.id)}
                        className="text-xs border border-zinc-200 text-zinc-500 hover:text-red-500 hover:border-red-200 px-3 py-1.5 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* RFQ Detail Modal */}
      {selectedRFQ && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100 sticky top-0 bg-white">
              <div>
                <span className="font-mono text-xs text-zinc-400">{selectedRFQ.rfq_number}</span>
                <h2 className="text-lg font-semibold text-zinc-900">{selectedRFQ.title}</h2>
              </div>
              <button onClick={() => setSelectedRFQ(null)} className="text-zinc-400 hover:text-zinc-600 text-xl">×</button>
            </div>
            <div className="px-6 py-5 space-y-5">
              {selectedRFQ.description && (
                <p className="text-sm text-zinc-600">{selectedRFQ.description}</p>
              )}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-zinc-400 text-xs mb-1">Deadline</p>
                  <p className="text-zinc-900">{new Date(selectedRFQ.deadline).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-zinc-400 text-xs mb-1">Status</p>
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[selectedRFQ.status]}`}>
                    {selectedRFQ.status?.replace('_', ' ')}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide mb-2">Items</p>
                <table className="w-full text-sm border border-zinc-100 rounded-lg overflow-hidden">
                  <thead>
                    <tr className="bg-zinc-50 border-b border-zinc-100">
                      <th className="text-left px-3 py-2 text-xs text-zinc-500">Item</th>
                      <th className="text-left px-3 py-2 text-xs text-zinc-500">Qty</th>
                      <th className="text-left px-3 py-2 text-xs text-zinc-500">Unit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRFQ.items?.map((item, i) => (
                      <tr key={i} className="border-b border-zinc-50 last:border-0">
                        <td className="px-3 py-2 text-zinc-900">{item.item_name}</td>
                        <td className="px-3 py-2 text-zinc-500">{item.quantity}</td>
                        <td className="px-3 py-2 text-zinc-500">{item.unit || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create RFQ Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100 sticky top-0 bg-white">
              <h2 className="text-lg font-semibold text-zinc-900">Create RFQ</h2>
              <button onClick={() => { setShowModal(false); reset() }} className="text-zinc-400 hover:text-zinc-600 text-xl">×</button>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="px-6 py-5 space-y-5">
              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Title</label>
                <input
                  placeholder="e.g. Office Furniture Procurement Q2"
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                  {...register('title', { required: 'Title is required' })}
                />
                {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title.message}</p>}
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Description</label>
                <textarea
                  rows={2}
                  placeholder="Describe the procurement requirement..."
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 resize-none"
                  {...register('description')}
                />
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Deadline</label>
                <input
                  type="datetime-local"
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                  {...register('deadline', { required: 'Deadline is required' })}
                />
                {errors.deadline && <p className="text-red-500 text-xs mt-1">{errors.deadline.message}</p>}
              </div>

              {/* Items */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-zinc-700">Line Items</label>
                  <button
                    type="button"
                    onClick={() => append({ item_name: '', quantity: 1, unit: 'pcs', description: '' })}
                    className="text-xs text-violet-600 hover:underline"
                  >
                    + Add item
                  </button>
                </div>
                <div className="space-y-2">
                  {fields.map((field, index) => (
                    <div key={field.id} className="flex gap-2 items-start">
                      <input
                        placeholder="Item name"
                        className="flex-1 border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                        {...register(`items.${index}.item_name`, { required: true })}
                      />
                      <input
                        type="number"
                        placeholder="Qty"
                        className="w-20 border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                        {...register(`items.${index}.quantity`, { required: true, min: 0.001 })}
                      />
                      <input
                        placeholder="Unit"
                        className="w-20 border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                        {...register(`items.${index}.unit`)}
                      />
                      {fields.length > 1 && (
                        <button
                          type="button"
                          onClick={() => remove(index)}
                          className="text-zinc-400 hover:text-red-500 px-2 py-2 text-lg leading-none"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Vendor selection */}
              {vendors.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-zinc-700 block mb-1.5">
                    Invite Vendors <span className="text-zinc-400 font-normal">(optional)</span>
                  </label>
                  <select
                    multiple
                    className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 h-28"
                    {...register('vendor_ids')}
                  >
                    {vendors.map((v) => (
                      <option key={v.id} value={v.id}>{v.company_name}</option>
                    ))}
                  </select>
                  <p className="text-zinc-400 text-xs mt-1">Hold Cmd/Ctrl to select multiple</p>
                </div>
              )}

              {createMutation.isError && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  <p className="text-red-600 text-sm">{createMutation.error?.response?.data?.message || 'Failed to create RFQ'}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); reset() }}
                  className="flex-1 border border-zinc-200 text-zinc-700 text-sm px-4 py-2 rounded-lg hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white text-sm px-4 py-2 rounded-lg disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create RFQ'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
