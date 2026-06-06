import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, Building2, FileText, ClipboardList,
  CheckSquare, ShoppingCart, Receipt, BarChart2, Bell, LogOut, Settings
} from 'lucide-react'
import { cn } from '@/lib/utils'
import useAuthStore from '../store/authStore'

const navSections = [
  {
    label: 'MAIN',
    items: [
      { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/rfqs', icon: FileText, label: 'RFQs' },
      { to: '/quotations', icon: ClipboardList, label: 'Quotations' },
      { to: '/approvals', icon: CheckSquare, label: 'Approvals' },
    ],
  },
  {
    label: 'VENDORS',
    items: [
      { to: '/vendors', icon: Building2, label: 'Vendors' },
    ],
  },
  {
    label: 'FINANCE',
    items: [
      { to: '/purchase-orders', icon: ShoppingCart, label: 'Purchase Orders' },
      { to: '/invoices', icon: Receipt, label: 'Invoices' },
      { to: '/reports', icon: BarChart2, label: 'Reports' },
    ],
  },
  {
    label: 'ADMIN',
    items: [
      { to: '/users', icon: Users, label: 'Users' },
    ],
    roles: ['admin'],
  },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-60 min-h-screen bg-zinc-950 text-zinc-400 flex flex-col border-r border-zinc-800">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-zinc-800">
        <span className="text-white font-semibold text-lg tracking-tight">
          ⬡ VendorBridge
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        {navSections.map((section) => {
          if (section.roles && !section.roles.includes(user?.role)) return null
          return (
            <div key={section.label} className="mb-6">
              <p className="px-3 mb-2 text-xs font-medium text-zinc-600 uppercase tracking-wider">
                {section.label}
              </p>
              {section.items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors mb-0.5',
                      isActive
                        ? 'bg-zinc-800 text-white'
                        : 'hover:bg-zinc-800/60 hover:text-zinc-200'
                    )
                  }
                >
                  <Icon size={16} />
                  {label}
                </NavLink>
              ))}
            </div>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-4 border-t border-zinc-800 space-y-1">
        <NavLink
          to="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-zinc-800/60 hover:text-zinc-200 transition-colors"
        >
          <Settings size={16} />
          Settings
        </NavLink>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-zinc-800/60 hover:text-red-400 transition-colors text-left"
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </aside>
  )
}
