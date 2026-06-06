import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { approvalApi } from '../api/approvalApi'
import useAuthStore from '../store/authStore'

const STATUS_COLORS = {
  pending: 'bg-amber-100 text-amber-700',
  approved: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
  cancelled: 'bg-zinc-100 text-zinc-500',
}

export default function Approvals() {
  const { user } = useAuthStore()
  const isManager = user?.role === 'manager'
  const isOfficer = user?.role === 'procurement_officer'
  const [actionModal, setActionModal] = useState(null)
  const [remarks, setRemarks] = useState('')
  const queryClient = useQueryClient()

  const { data: pendingData, isLoading: pendingLoading } = useQuery({
    queryKey: ['approvals-pending'],
    queryFn: () => approvalApi.getPending().then(r => r.data),
    enabled: isManager,
  })

  const { data: allData, isLoading: allLoading } = useQuery({
    queryKey: ['approvals-all'],
    queryFn: () => approvalApi.getAll().then(r => r.data),
    enabled: isOfficer,
  })

  const actionMutation = useMutation({
    mutationFn: ({ id, action, remarks }) => approvalApi.action(id, { action, remarks }),
    onSuccess: () => {
      queryClient.invalidateQueries(['approvals-pending'])
      queryClient.invalidateQueries(['approvals-all'])
      setActionModal(null)
      setRemarks('')
    },
  })

  const workflows = isManager
    ? (pendingData?.data || [])
    : (allData?.data || [])

  const isLoading = isManager ? pendingLoading : allLoading

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">Approvals</h1>
          <p className="text-zinc-500 text-sm mt-1">
            {isManager ? 'Review and approve procurement requests' : 'Track your initiated approval workflows'}
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="bg-white rounded-xl border border-zinc-200 py-16 text-center text-zinc-400 text-sm">
          Loading...
        </div>
      ) : workflows.length === 0 ? (
        <div className="bg-white rounded-xl border border-zinc-200 py-16 text-center">
          <p className="text-zinc-400 text-sm">
            {isManager ? 'No pending approvals.' : 'No workflows initiated yet.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="bg-white rounded-xl border border-zinc-200 p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-zinc-900 text-sm">
                    Quotation: <span className="font-mono">{workflow.quotation_id}</span>
                  </p>
                  <p className="text-zinc-500 text-xs mt-1">
                    Step {workflow.current_step} of {workflow.total_steps}
                  </p>
                </div>
                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[workflow.status]}`}>
                  {workflow.status}
                </span>
              </div>

              {/* Steps timeline */}
              <div className="flex items-center gap-2 mt-4">
                {workflow.steps?.map((step, idx) => (
                  <div key={step.id} className="flex items-center gap-2">
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium ${
                      step.action === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                      step.action === 'rejected' ? 'bg-red-100 text-red-700' :
                      'bg-zinc-100 text-zinc-500'
                    }`}>
                      {step.step_number}
                    </div>
                    {idx < workflow.steps.length - 1 && (
                      <div className="w-8 h-px bg-zinc-200" />
                    )}
                  </div>
                ))}
              </div>

              {isManager && workflow.status === 'pending' && (
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => setActionModal({ workflow, action: 'approved' })}
                    className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-3 py-1.5 rounded-lg transition-colors"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => setActionModal({ workflow, action: 'rejected' })}
                    className="flex items-center gap-1.5 bg-red-500 hover:bg-red-600 text-white text-xs px-3 py-1.5 rounded-lg transition-colors"
                  >
                    ✕ Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Action Modal */}
      {actionModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100">
              <h2 className="text-lg font-semibold text-zinc-900 capitalize">
                {actionModal.action === 'approved' ? 'Approve' : 'Reject'} workflow
              </h2>
              <button onClick={() => { setActionModal(null); setRemarks('') }} className="text-zinc-400 hover:text-zinc-600 text-xl">×</button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">
                  Remarks {actionModal.action === 'rejected' && <span className="text-red-500">*</span>}
                </label>
                <textarea
                  rows={3}
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="Add your remarks..."
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 resize-none"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => { setActionModal(null); setRemarks('') }}
                  className="flex-1 border border-zinc-200 text-zinc-700 text-sm px-4 py-2 rounded-lg hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => actionMutation.mutate({
                    id: actionModal.workflow.id,
                    action: actionModal.action,
                    remarks
                  })}
                  disabled={actionMutation.isPending}
                  className={`flex-1 text-white text-sm px-4 py-2 rounded-lg transition-colors disabled:opacity-50 ${
                    actionModal.action === 'approved'
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-red-500 hover:bg-red-600'
                  }`}
                >
                  {actionMutation.isPending ? 'Submitting...' : 'Confirm'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
