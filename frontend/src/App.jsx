import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Login from './pages/auth/Login'
import Dashboard from './pages/Dashboard'
import Users from './pages/admin/Users'
import Vendors from './pages/Vendors'
import Approvals from './pages/Approvals'
import RFQs from './pages/RFQs'
import Quotations from './pages/Quotations'
import PurchaseOrders from './pages/PurchaseOrders'
import Invoices from './pages/Invoices'
import ActivityLogs from './pages/ActivityLogs'
import Reports from './pages/Reports'
import useAuthStore from './store/authStore'

const queryClient = new QueryClient()

function ProtectedRoute({ children }) {
  const { token } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  return children
}

function AdminRoute({ children }) {
  const { token, user } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />
  return children
}

function PublicRoute({ children }) {
  const { token } = useAuthStore()
  if (token) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/app" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
          </Route>
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="vendors" element={<Vendors />} />
            <Route path="approvals" element={<Approvals />} />
            <Route path="rfqs" element={<RFQs />} />
            <Route path="quotations" element={<Quotations />} />
            <Route path="purchase-orders" element={<PurchaseOrders />} />
            <Route path="invoices" element={<Invoices />} />
            <Route path="activity" element={<ActivityLogs />} />
            <Route path="reports" element={<Reports />} />
            <Route path="users" element={<AdminRoute><Users /></AdminRoute>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
