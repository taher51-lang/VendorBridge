import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../../api/authApi'

const ROLES = [
  { value: 'procurement_officer', label: 'Procurement Officer' },
  { value: 'manager', label: 'Manager' },
  { value: 'vendor', label: 'Vendor' },
]

const ROLE_COLORS = {
  admin: 'bg-violet-100 text-violet-700',
  procurement_officer: 'bg-blue-100 text-blue-700',
  manager: 'bg-amber-100 text-amber-700',
  vendor: 'bg-emerald-100 text-emerald-700',
}

const ROLE_LABELS = {
  admin: 'Admin',
  procurement_officer: 'Procurement Officer',
  manager: 'Manager',
  vendor: 'Vendor',
}

export default function Users() {
  const [showModal, setShowModal] = useState(false)
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const { register, handleSubmit, reset, formState: { errors } } = useForm()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (data) => authApi.register(data),
    onSuccess: (res) => {
      const newUser = res.data.data
      setUsers((prev) => [newUser, ...prev])
      setSuccess(`User ${newUser.full_name} created successfully.`)
      setError('')
      reset()
      setShowModal(false)
      setTimeout(() => setSuccess(''), 3000)
    },
    onError: (err) => {
      setError(err.response?.data?.message || 'Failed to create user.')
    },
  })

  const onSubmit = (data) => {
    setError('')
    createMutation.mutate(data)
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">User Management</h1>
          <p className="text-zinc-500 text-sm mt-1">Create and manage system users</p>
        </div>
        <button
          onClick={() => { setShowModal(true); setError('') }}
          className="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 text-white text-sm px-4 py-2 rounded-lg transition-colors"
        >
          + Add User
        </button>
      </div>

      {/* Success banner */}
      {success && (
        <div className="mb-4 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
          <p className="text-emerald-700 text-sm">{success}</p>
        </div>
      )}

      {/* Users table */}
      <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        {users.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-zinc-400 text-sm">No users created yet.</p>
            <p className="text-zinc-400 text-xs mt-1">Click "Add User" to create your first user.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-100 bg-zinc-50">
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Name</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Email</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Role</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Status</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wide">Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-zinc-100 last:border-0 hover:bg-zinc-50">
                  <td className="px-5 py-3.5 font-medium text-zinc-900">{user.full_name}</td>
                  <td className="px-5 py-3.5 text-zinc-500">{user.email}</td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_COLORS[user.role]}`}>
                      {ROLE_LABELS[user.role]}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${user.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-zinc-500">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100">
              <h2 className="text-lg font-semibold text-zinc-900">Create new user</h2>
              <button
                onClick={() => { setShowModal(false); setError(''); reset() }}
                className="text-zinc-400 hover:text-zinc-600 text-xl leading-none"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="px-6 py-5 space-y-4">
              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Full name</label>
                <input
                  placeholder="John Smith"
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                  {...register('full_name', { required: 'Full name is required' })}
                />
                {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Email</label>
                <input
                  type="email"
                  placeholder="john@company.com"
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                  {...register('email', { required: 'Email is required' })}
                />
                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Phone</label>
                <input
                  placeholder="+91 98765 43210"
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                  {...register('phone')}
                />
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Role</label>
                <select
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent bg-white"
                  {...register('role', { required: 'Role is required' })}
                >
                  <option value="">Select a role</option>
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
                {errors.role && <p className="text-red-500 text-xs mt-1">{errors.role.message}</p>}
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">
                  Temporary password
                </label>
                <input
                  type="password"
                  placeholder="Min. 8 characters"
                  className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: { value: 8, message: 'Min. 8 characters' }
                  })}
                />
                {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setError(''); reset() }}
                  className="flex-1 border border-zinc-200 text-zinc-700 text-sm px-4 py-2 rounded-lg hover:bg-zinc-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white text-sm px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create user'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
