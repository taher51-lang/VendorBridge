import useAuthStore from '../store/authStore'

export default function Dashboard() {
  const { user } = useAuthStore()

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900">Dashboard</h1>
        <p className="text-zinc-500 text-sm mt-1">
          Welcome back, {user?.full_name}. Here's what's happening.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Active RFQs', value: '—' },
          { label: 'Pending Approvals', value: '—' },
          { label: 'Recent POs', value: '—' },
          { label: 'Invoices', value: '—' },
        ].map((card) => (
          <div
            key={card.label}
            className="bg-white rounded-xl border border-zinc-200 p-5"
          >
            <p className="text-sm text-zinc-500 mb-1">{card.label}</p>
            <p className="text-2xl font-semibold text-zinc-900">{card.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
