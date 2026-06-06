import { Bell, Settings } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import useAuthStore from '../store/authStore'

export default function Navbar() {
  const { user } = useAuthStore()

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U'

  const roleLabel = {
    admin: 'Admin',
    procurement_officer: 'Procurement Officer',
    manager: 'Manager',
    vendor: 'Vendor',
  }[user?.role] || ''

  return (
    <header className="h-14 border-b border-zinc-200 bg-white flex items-center justify-between px-6">
      <div className="text-sm text-zinc-500">
        Welcome back, <span className="font-medium text-zinc-800">{user?.full_name || 'User'}</span>
      </div>

      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-lg hover:bg-zinc-100 transition-colors">
          <Bell size={18} className="text-zinc-500" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        <div className="flex items-center gap-2.5">
          <Avatar className="w-8 h-8">
            <AvatarFallback className="bg-violet-100 text-violet-700 text-xs font-medium">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-zinc-800 leading-tight">{user?.full_name}</p>
            <p className="text-xs text-zinc-500 leading-tight">{roleLabel}</p>
          </div>
        </div>
      </div>
    </header>
  )
}
