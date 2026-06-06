import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { invoiceApi } from '../api/invoiceApi'
import { Receipt, Eye, Download, Send, CreditCard, X, Search, Ban } from 'lucide-react'
import useAuthStore from '../store/authStore'

const STATUS_STYLES = {
  draft: 'bg-zinc-100 text-zinc-600',
  sent: 'bg-blue-100 text-blue-700',
  paid: 'bg-emerald-100 text-emerald-700',
  overdue: 'bg-amber-100 text-amber-700',
  cancelled: 'bg-rose-100 text-rose-700',
}

const STATUS_TABS = ['all', 'draft', 'sent', 'paid', 'overdue', 'cancelled']

function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLES[status] || 'bg-zinc-100 text-zinc-600'}`}>
      {status}
    </span>
  )
}

export default function Invoices() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [search, setSearch] = useState('')
  const [selectedInvoice, setSelectedInvoice] = useState(null)
  const [showSendModal, setShowSendModal] = useState(false)
  const [sendEmail, setSendEmail] = useState('')
  const [sendSubject, setSendSubject] = useState('')
  const [page, setPage] = useState(1)

  const isOfficer = ['procurement_officer', 'admin'].includes(user?.role)
  const isVendor = user?.role === 'vendor'

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', activeTab, page],
    queryFn: () => {
      const params = { page, per_page: 15 }
      if (activeTab !== 'all') params.status = activeTab
      return invoiceApi.getAll(params).then(r => r.data)
    },
  })

  const markPaidMutation = useMutation({
    mutationFn: (id) => invoiceApi.markPaid(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setSelectedInvoice(null)
    },
  })

  const cancelMutation = useMutation({
    mutationFn: (id) => invoiceApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setSelectedInvoice(null)
    },
  })

  const sendMutation = useMutation({
    mutationFn: ({ id, data }) => invoiceApi.send(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setShowSendModal(false)
      setSendEmail('')
      setSendSubject('')
    },
  })

  const handleDownloadPdf = async (invoiceId) => {
    try {
      const response = await invoiceApi.generatePdf(invoiceId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `invoice-${invoiceId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('PDF download failed:', err)
    }
  }

  const invoices = data?.data || []
  const meta = data?.meta || {}

  const filtered = search
    ? invoices.filter(inv =>
      inv.invoice_number?.toLowerCase().includes(search.toLowerCase()) ||
      inv.vendor_name?.toLowerCase().includes(search.toLowerCase())
    )
    : invoices

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2">
          <Receipt size={22} className="text-violet-500" />
          Invoices
        </h1>
        <p className="text-zinc-500 text-sm mt-1">
          {isVendor ? 'View invoices for your orders.' : 'Generate, send, and track invoices.'}
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
            placeholder="Search invoices..."
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
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center">
            <Receipt size={40} className="mx-auto text-zinc-300 mb-3" />
            <p className="text-zinc-500 text-sm">No invoices found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs text-zinc-500 border-b border-zinc-100 bg-zinc-50/50">
                <th className="px-5 py-3 font-medium">Invoice #</th>
                <th className="px-5 py-3 font-medium">PO Ref</th>
                {!isVendor && <th className="px-5 py-3 font-medium">Vendor</th>}
                <th className="px-5 py-3 font-medium">Total</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Date</th>
                <th className="px-5 py-3 font-medium">Due</th>
                <th className="px-5 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(inv => (
                <tr key={inv.id} className="border-b border-zinc-50 hover:bg-zinc-50/50 transition-colors">
                  <td className="px-5 py-3.5 text-sm font-medium text-zinc-800">{inv.invoice_number}</td>
                  <td className="px-5 py-3.5 text-sm text-zinc-600">{inv.po_number || '—'}</td>
                  {!isVendor && <td className="px-5 py-3.5 text-sm text-zinc-600">{inv.vendor_name || '—'}</td>}
                  <td className="px-5 py-3.5 text-sm font-medium text-zinc-800">
                    ₹{Number(inv.total_amount || 0).toLocaleString('en-IN')}
                  </td>
                  <td className="px-5 py-3.5"><StatusBadge status={inv.status} /></td>
                  <td className="px-5 py-3.5 text-sm text-zinc-500">
                    {inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-zinc-500">
                    {inv.due_date ? new Date(inv.due_date).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => setSelectedInvoice(inv)}
                        className="p-1.5 rounded-md hover:bg-zinc-100 text-zinc-500 hover:text-zinc-700"
                        title="View"
                      >
                        <Eye size={15} />
                      </button>
                      {isOfficer && (
                        <>
                          <button
                            onClick={() => handleDownloadPdf(inv.id)}
                            className="p-1.5 rounded-md hover:bg-blue-50 text-blue-600 hover:text-blue-800"
                            title="Download PDF"
                          >
                            <Download size={15} />
                          </button>
                          {['draft', 'sent'].includes(inv.status) && (
                            <button
                              onClick={() => { setSelectedInvoice(inv); setShowSendModal(true) }}
                              className="p-1.5 rounded-md hover:bg-violet-50 text-violet-600 hover:text-violet-800"
                              title="Send Email"
                            >
                              <Send size={15} />
                            </button>
                          )}
                          {['sent', 'overdue', 'draft'].includes(inv.status) && (
                            <button
                              onClick={() => markPaidMutation.mutate(inv.id)}
                              className="p-1.5 rounded-md hover:bg-emerald-50 text-emerald-600 hover:text-emerald-800"
                              title="Mark Paid"
                              disabled={markPaidMutation.isPending}
                            >
                              <CreditCard size={15} />
                            </button>
                          )}
                          {['draft', 'sent'].includes(inv.status) && (
                            <button
                              onClick={() => cancelMutation.mutate(inv.id)}
                              className="p-1.5 rounded-md hover:bg-rose-50 text-rose-500 hover:text-rose-700"
                              title="Cancel"
                              disabled={cancelMutation.isPending}
                            >
                              <Ban size={15} />
                            </button>
                          )}
                        </>
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

      {/* Detail Modal */}
      {selectedInvoice && !showSendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setSelectedInvoice(null)}>
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-900">{selectedInvoice.invoice_number}</h2>
              <button onClick={() => setSelectedInvoice(null)} className="p-1 hover:bg-zinc-100 rounded-lg">
                <X size={18} className="text-zinc-400" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-zinc-500 mb-0.5">Status</p>
                  <StatusBadge status={selectedInvoice.status} />
                </div>
                <div>
                  <p className="text-zinc-500 mb-0.5">PO Reference</p>
                  <p className="font-medium text-zinc-800">{selectedInvoice.po_number || '—'}</p>
                </div>
                <div>
                  <p className="text-zinc-500 mb-0.5">Invoice Date</p>
                  <p className="font-medium text-zinc-800">{selectedInvoice.invoice_date || '—'}</p>
                </div>
                <div>
                  <p className="text-zinc-500 mb-0.5">Due Date</p>
                  <p className="font-medium text-zinc-800">{selectedInvoice.due_date || '—'}</p>
                </div>
              </div>
              <div className="border-t border-zinc-100 pt-4">
                <h3 className="text-sm font-semibold text-zinc-900 mb-2">GST Breakdown</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-zinc-50 rounded-lg p-3">
                    <p className="text-zinc-500 text-xs">Subtotal</p>
                    <p className="font-semibold">₹{Number(selectedInvoice.subtotal || 0).toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-zinc-50 rounded-lg p-3">
                    <p className="text-zinc-500 text-xs">CGST</p>
                    <p className="font-semibold">₹{Number(selectedInvoice.cgst_amount || 0).toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-zinc-50 rounded-lg p-3">
                    <p className="text-zinc-500 text-xs">SGST</p>
                    <p className="font-semibold">₹{Number(selectedInvoice.sgst_amount || 0).toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-zinc-50 rounded-lg p-3">
                    <p className="text-zinc-500 text-xs">IGST</p>
                    <p className="font-semibold">₹{Number(selectedInvoice.igst_amount || 0).toLocaleString('en-IN')}</p>
                  </div>
                </div>
                <div className="mt-2 bg-violet-50 rounded-lg p-3 text-center">
                  <p className="text-violet-500 text-xs">Total Amount</p>
                  <p className="text-xl font-bold text-violet-800">₹{Number(selectedInvoice.total_amount || 0).toLocaleString('en-IN')}</p>
                </div>
              </div>
              {selectedInvoice.items?.length > 0 && (
                <div className="border-t border-zinc-100 pt-4">
                  <h3 className="text-sm font-semibold text-zinc-900 mb-2">Line Items</h3>
                  <div className="space-y-2">
                    {selectedInvoice.items.map((item, i) => (
                      <div key={i} className="flex items-center justify-between text-sm bg-zinc-50 rounded-lg px-3 py-2">
                        <div>
                          <p className="font-medium text-zinc-800">{item.item_name}</p>
                          <p className="text-xs text-zinc-500">Qty: {item.quantity} × ₹{item.unit_price} (Tax: {item.tax_rate}%)</p>
                        </div>
                        <p className="font-medium text-zinc-800">₹{Number(item.line_total || 0).toLocaleString('en-IN')}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Send Email Modal */}
      {showSendModal && selectedInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => { setShowSendModal(false); setSelectedInvoice(null) }}>
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-900">Send Invoice</h2>
              <button onClick={() => { setShowSendModal(false); setSelectedInvoice(null) }} className="p-1 hover:bg-zinc-100 rounded-lg">
                <X size={18} className="text-zinc-400" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-zinc-600">
                Sending <span className="font-medium">{selectedInvoice.invoice_number}</span> via email.
              </p>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Recipient Email *</label>
                <input
                  type="email"
                  value={sendEmail}
                  onChange={e => setSendEmail(e.target.value)}
                  placeholder="vendor@example.com"
                  className="w-full px-3 py-2 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Subject (optional)</label>
                <input
                  type="text"
                  value={sendSubject}
                  onChange={e => setSendSubject(e.target.value)}
                  placeholder="Invoice from VendorBridge"
                  className="w-full px-3 py-2 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-400"
                />
              </div>
              <button
                onClick={() => sendMutation.mutate({
                  id: selectedInvoice.id,
                  data: { recipient_email: sendEmail, subject: sendSubject || undefined }
                })}
                disabled={!sendEmail || sendMutation.isPending}
                className="w-full py-2.5 bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {sendMutation.isPending ? 'Sending...' : 'Send Invoice'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
