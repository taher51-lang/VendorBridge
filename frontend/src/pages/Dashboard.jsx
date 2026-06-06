import useAuthStore from '../store/authStore'
import AdminDashboard from './dashboard/AdminDashboard'
import OfficerDashboard from './dashboard/OfficerDashboard'
import ManagerDashboard from './dashboard/ManagerDashboard'
import VendorDashboard from './dashboard/VendorDashboard'

export default function Dashboard() {
  const { user } = useAuthStore()

  const dashboards = {
    admin: AdminDashboard,
    procurement_officer: OfficerDashboard,
    manager: ManagerDashboard,
    vendor: VendorDashboard,
  }

  const DashboardComponent = dashboards[user?.role] || OfficerDashboard

  return <DashboardComponent />
}
