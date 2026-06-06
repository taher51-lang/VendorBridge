import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useFieldArray } from 'react-hook-form'
import { quotationApi } from '../api/quotationApi'
import { rfqApi } from '../api/rfqApi'
import { approvalApi } from '../api/approvalApi'
import useAuthStore from '../store/authStore'

const STATUS_COLORS = {
  draft: 'bg-zinc-100 text-zinc-600',
  submitted: 'bg-blue-100 text-blue-700',
  selected: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
}

export default function Quotations() {
  const { user } = useAuthStore()
  const isVendor = user?.role === 'vendor'
  const isOfficer = user?.role === 'procurement_officer' || user?.role === 'admin'
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [compareRFQId, setCompareRFQId] = useState(null)
  const [approvalModal, setApprovalModal] = useState(null)
  const [approverIds, setApproverIds] = useState([''])
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['quotations'],
    queryFn: () => quotationApi.getAll({ per_page: 50 }).then(r => r.data),
  })

  const { data: rfqData } = useQuery({
    queryKey: ['rfqs-open'],
    queryFn: () => rfqApi.getAll({ status: 'open', per_page: 100 }).then(r => r.data),
    enabled: isVendor,
  })

  const { data: compareData } = useQuery({
    queryKey: ['compare', compareRFQId],
    queryFn: () => quotationApi.compare(compareRFQId).then(r => r.data),
    enabled: !!compareRFQId,
  })

  const quotations = data?.data || []
  const openRFQs = rfqData?.data || []
  const comparison = compareData?.data

  const { register, control, handleSubmit, watch, reset, formState: { errors } } = useForm({
    defaultValues: {
      delivery_days: 7,
      validity_days: 30,
      currency: 'INR',
      is_interstate: false,
      items: [{ unit_price: '', quantity: 1, tax_rate: 18, notes: '' }]
    }
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'items' })
  const selectedRFQId = watch('rfq_id')
  const selectedRFQ = openRFQs.find(r => r.id === selectedRFQId)

  const createMutation = useMutation({
    mutationFn: (data) => quotationApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['quotations'])
      setShowCreateModal(false)
      reset()
    },
  })

  const submitMutation = useMutation({
    mutationFn: (id) => quotationApi.submit(id),
    onSuccess: () => queryClient.invalidateQueries(['quotations']),
  })

  const selectMutation = useMutation({
    mutationFn: (id) => quotationApi.select(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries(['quotations'])
      setApprovalModal({ quotation_id: id })
    },
  })

  const initiateMutation = useMutation({
    mutationFn: (data) => approvalApi.initiate(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['quotations'])
      setApprovalModal(null)
      setApproverIds([''])
    },
  })

  const onSubmit = (data) => {
    const items = data.items.map((item, idx) => ({
      rfq_item_id: selectedRFQ?.items?.[idx]?.id || null,
      unit_price: String(item.unit_price),
      quantity: String(item.quantity),
      tax_rate: String(item.tax_rate || 0),
      notes: item.notes || null,
    }))
    createMutation.mutate({ ...data, items })
  }

  const handleInitiateApproval = () => {
    const steps = approverIds
      .filter(id => id.trim())
      .map((approver_id, idx) => ({ step_number: idx + 1, approver_id }))
    initiateMutation.mutate({
      quotation_id: approvalModal.quotation_id,
      steps,
    })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">Quotations</h1>
          <p className="text-zinc-500 text-sm mt-1">
            {isVendor ? 'Submit and manage your quotations' : 'Review and compare vendor quotations'}
          </p>
        </div>
        {isVendor && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-zinc-900 hover:bg-zinc-800 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            + Submit Quotation
          </button>
        )}
      </div>

      {/* Quotations list */}
      {isLoading ? (
        <div className="bg-white rounded-xl border border-zinc-200 py-16 text-center text-zinc-400 text-sm">Loading...</div>
      ) : quotations.length === 0 ? (
        <div className="bg-white rounded-xl border border-zinc-200 py-16 text-center text-zinc-400 text-sm">
          No quotations yet.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-zinc-50 border-b border-zinc-100">
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Quote #</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">RFQ</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Total</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Delivery</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Status</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody>
              {quotations.map((q) => (
                <tr key={q.id} className="border-b border-zinc-100 last:border-0 hover:bg-zinc-50">
                  <td className="px-5 py-3.5 font-mono text-xs text-zinc-500">{q.quote_number}</td>
                  <td className="px-5 py-3.5 text-zinc-700 font-mono text-xs">{q.rfq_id?.slice(0, 8)}...</td>
                  <td className="px-5 py-3.5 font-medium text-zinc-900">
                    ₹{parseFloat(q.total_amount || 0).toLocaleString('en-IN')}
                  </td>
                  <td className="px-5 py-3.5 text-zinc-500">{q.delivery_days} days</td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[q.status]}`}>
                      {q.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex gap-2">
                      {isVendor && q.status === 'draft' && (
                        <button
                          onClick={() => submitMutation.mutate(q.id)}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Submit
                        </button>
                      )}
                      {isOfficer && q.status === 'submitted' && (
                        <>
                          <button
                            onClick={() => setCompareRFQId(q.rfq_id)}
                            className="text-xs text-violet-600 hover:underline"
                          >
                            Compare
                          </button>
                          <button
                            onClick={() => selectMutation.mutate(q.id)}
                            className="text-xs text-emerald-600 hover:underline"
                          >
                            Select
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Comparison Modal */}
      {compareRFQId && comparison && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-4xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100 sticky top-0 bg-white">
              <h2 className="text-lg font-semibold text-zinc-900">Quotation Comparison</h2>
              <button onClick={() => setCompareRFQId(null)} className="text-zinc-400 hover:text-zinc-600 text-xl">×</button>
            </div>
            <div className="px-6 py-5 overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b border-zinc-200">
                    <th className="text-left py-3 pr-4 text-xs font-medium text-zinc-500 uppercase">Metric</th>
                    {comparison.quotations?.map((q) => (
                      <th key={q.id} className={`text-left py-3 px-4 text-xs font-medium uppercase ${
                        q.id === comparison.recommended_quotation_id
                          ? 'text-emerald-700 bg-emerald-50 rounded-t-lg'
                          : 'text-zinc-500'
                      }`}>
                        {q.quote_number}
                        {q.id === comparison.recommended_quotation_id && (
                          <span className="ml-1 text-emerald-600">★ Best</span>
                        )}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: 'Total Amount', key: 'total_amount', format: (v) => `₹${parseFloat(v).toLocaleString('en-IN')}` },
                    { label: 'Subtotal', key: 'subtotal', format: (v) => `₹${parseFloat(v).toLocaleString('en-IN')}` },
                    { label: 'Tax', key: 'tax_amount', format: (v) => `₹${parseFloat(v).toLocaleString('en-IN')}` },
                    { label: 'Delivery Days', key: 'delivery_days', format: (v) => `${v} days` },
                    { label: 'Validity', key: 'validity_days', format: (v) => v ? `${v} days` : '—' },
                    { label: 'Currency', key: 'currency', format: (v) => v },
                  ].map((row) => {
                    const values = comparison.quotations?.map(q => parseFloat(q[row.key] || 0))
                    const minVal = Math.min(...values)
                    return (
                      <tr key={row.label} className="border-b border-zinc-100">
                        <td className="py-3 pr-4 text-zinc-500 text-xs">{row.label}</td>
                        {comparison.quotations?.map((q, i) => (
                          <td key={q.id} className={`py-3 px-4 font-medium ${
                            q.id === comparison.recommended_quotation_id ? 'bg-emerald-50' : ''
                          } ${
                            (row.key === 'total_amount' || row.key === 'delivery_days') && values[i] === minVal
                              ? 'text-emerald-600'
                              : 'text-zinc-900'
                          }`}>
                            {row.format(q[row.key])}
                          </td>
                        ))}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Initiate Approval Modal */}
      {approvalModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100">
              <h2 className="text-lg font-semibold text-zinc-900">Initiate Approval</h2>
              <button onClick={() => setApprovalModal(null)} className="text-zinc-400 hover:text-zinc-600 text-xl">×</button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <p className="text-sm text-zinc-600">Add approvers in sequence. They will be notified in order.</p>
              {approverIds.map((id, idx) => (
                <div key={idx} className="flex gap-2">
                  <input
                    value={id}
                    onChange={(e) => {
                      const updated = [...approverIds]
                      updated[idx] = e.target.value
                      setApproverIds(updated)
                    }}
                    placeholder={`Step ${idx + 1} — Approver User ID`}
                    className="flex-1 border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 font-mono"
                  />
                  {approverIds.length > 1 && (
                    <button
                      onClick={() => setApproverIds(approverIds.filter((_, i) => i !== idx))}
                      className="text-zinc-400 hover:text-red-500 px-2"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button
                onClick={() => setApproverIds([...approverIds, ''])}
                className="text-xs text-violet-600 hover:underline"
              >
                + Add another approver
              </button>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setApprovalModal(null)}
                  className="flex-1 border border-zinc-200 text-zinc-700 text-sm px-4 py-2 rounded-lg hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleInitiateApproval}
                  disabled={initiateMutation.isPending}
                  className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white text-sm px-4 py-2 rounded-lg disabled:opacity-50"
                >
                  {initiateMutation.isPending ? 'Initiating...' : 'Initiate Approval'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Quotation Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100 sticky top-0 bg-white">
              <h2 className="text-lg font-semibold text-zinc-900">Submit Quotation</h2>
              <button onClick={() => { setShowCreateModal(false); reset() }} className="text-zinc-400 hover:text-zinc-600 text-xl">×</button>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="px-6 py-5 space-y-4">
              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">RFQ</label>
                <select
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 bg-white"
                  {...register('rfq_id', { required: 'Please select an RFQ' })}
                >
                  <option value="">Select an RFQ</option>
                  {openRFQs.map((rfq) => (
                    <option key={rfq.id} value={rfq.id}>{rfq.rfq_number} — {rfq.title}</option>
                  ))}
                </select>
                {errors.rfq_id && <p className="text-red-500 text-xs mt-1">{errors.rfq_id.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-zinc-700 block mb-1.5">Delivery Days</label>
                  <input
                    type="number"
                    className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                    {...register('delivery_days', { required: true, min: 1 })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-zinc-700 block mb-1.5">Validity Days</label>
                  <input
                    type="number"
                    className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                    {...register('validity_days')}
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input type="checkbox" id="interstate" {...register('is_interstate')} />
                <label htmlFor="interstate" className="text-sm text-zinc-700">Interstate transaction (IGST applies)</label>
              </div>

              {/* Items */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-zinc-700">
                    {selectedRFQ ? `Items (${selectedRFQ.items?.length} required)` : 'Items'}
                  </label>
                  {!selectedRFQ && (
                    <button type="button" onClick={() => append({ unit_price: '', quantity: 1, tax_rate: 18 })} className="text-xs text-violet-600 hover:underline">
                      + Add item
                    </button>
                  )}
                </div>
                <div className="space-y-2">
                  {fields.map((field, index) => (
                    <div key={field.id} className="border border-zinc-100 rounded-lg p-3 space-y-2">
                      {selectedRFQ?.items?.[index] && (
                        <p className="text-xs text-zinc-500 font-medium">
                          {selectedRFQ.items[index].item_name} — {selectedRFQ.items[index].quantity} {selectedRFQ.items[index].unit}
                        </p>
                      )}
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <input
                            type="number"
                            step="0.01"
                            placeholder="Unit price (₹)"
                            className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                            {...register(`items.${index}.unit_price`, { required: true })}
                          />
                        </div>
                        <div className="w-24">
                          <input
                            type="number"
                            step="0.001"
                            placeholder="Qty"
                            className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                            {...register(`items.${index}.quantity`, { required: true })}
                          />
                        </div>
                        <div className="w-24">
                          <input
                            type="number"
                            step="0.01"
                            placeholder="Tax %"
                            className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                            {...register(`items.${index}.tax_rate`)}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Notes</label>
                <textarea
                  rows={2}
                  placeholder="Any additional terms or notes..."
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 resize-none"
                  {...register('notes')}
                />
              </div>

              {createMutation.isError && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  <p className="text-red-600 text-sm">{createMutation.error?.response?.data?.message || 'Failed to submit quotation'}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowCreateModal(false); reset() }}
                  className="flex-1 border border-zinc-200 text-zinc-700 text-sm px-4 py-2 rounded-lg hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white text-sm px-4 py-2 rounded-lg disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Submitting...' : 'Save as Draft'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
