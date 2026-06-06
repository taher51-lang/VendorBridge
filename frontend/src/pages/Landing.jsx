import { useNavigate } from 'react-router-dom'
import { ArrowRight, Shield, FileText, ShoppingCart, Receipt, BarChart2, Users, Zap, CheckCircle2 } from 'lucide-react'
import useAuthStore from '../store/authStore'
import { useEffect } from 'react'

const features = [
  { icon: FileText, title: 'RFQ Management', desc: 'Create and distribute Requests for Quotation to multiple vendors simultaneously.' },
  { icon: Users, title: 'Vendor Portal', desc: 'Vendors submit quotations, track POs, and manage their profiles in one place.' },
  { icon: Shield, title: 'Approval Workflows', desc: 'Multi-level approval chains with role-based access and audit trails.' },
  { icon: ShoppingCart, title: 'Purchase Orders', desc: 'Auto-generate POs from approved quotations with full lifecycle tracking.' },
  { icon: Receipt, title: 'GST Invoicing', desc: 'Generate GST-compliant invoices with CGST/SGST/IGST breakdown and PDF export.' },
  { icon: BarChart2, title: 'Analytics & Reports', desc: 'Spend analysis, vendor performance, and monthly procurement trend dashboards.' },
]

const stats = [
  { value: '4', label: 'User Roles' },
  { value: '8+', label: 'Modules' },
  { value: '100%', label: 'GST Compliant' },
  { value: '∞', label: 'Scalable' },
]

const workflow = [
  'RFQ Created',
  'Vendors Invited',
  'Quotations Submitted',
  'Quotations Compared',
  'Approval Workflow',
  'PO Generated',
  'Invoice & PDF',
]

export default function Landing() {
  const navigate = useNavigate()
  const { token } = useAuthStore()

  useEffect(() => {
    if (token) navigate('/dashboard', { replace: true })
  }, [token, navigate])

  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-zinc-100">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-bold text-zinc-900 tracking-tight">⬡ VendorBridge</span>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
            >
              Sign in
            </button>
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 text-sm font-medium text-white bg-zinc-900 hover:bg-zinc-800 rounded-lg transition-colors"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-violet-50 border border-violet-200 rounded-full text-xs font-medium text-violet-700 mb-6">
            <Zap size={12} />
            Procurement Made Simple
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold text-zinc-900 tracking-tight leading-[1.1] mb-6">
            Procurement & Vendor
            <br />
            <span className="bg-gradient-to-r from-violet-600 to-blue-600 bg-clip-text text-transparent">
              Management ERP
            </span>
          </h1>
          <p className="text-lg text-zinc-500 max-w-2xl mx-auto mb-10 leading-relaxed">
            Streamline your entire procurement lifecycle — from RFQ creation to invoice generation.
            Built for teams that need transparency, compliance, and speed.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => navigate('/login')}
              className="group px-6 py-3 text-sm font-medium text-white bg-zinc-900 hover:bg-zinc-800 rounded-xl transition-all shadow-lg shadow-zinc-900/10 flex items-center gap-2"
            >
              Open Dashboard
              <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
            </button>
            <a
              href="#features"
              className="px-6 py-3 text-sm font-medium text-zinc-600 border border-zinc-200 hover:border-zinc-300 rounded-xl transition-colors"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 border-y border-zinc-100 bg-zinc-50/50">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 sm:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <div key={i} className="text-center">
              <p className="text-3xl font-bold text-zinc-900">{s.value}</p>
              <p className="text-sm text-zinc-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Workflow */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-zinc-900 text-center mb-3">End-to-End Workflow</h2>
          <p className="text-zinc-500 text-center mb-12 max-w-lg mx-auto">
            A complete procurement pipeline from requisition to payment.
          </p>
          <div className="flex items-center justify-center flex-wrap gap-2">
            {workflow.map((step, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-4 py-2.5 bg-white border border-zinc-200 rounded-xl shadow-sm">
                  <CheckCircle2 size={14} className="text-violet-500 shrink-0" />
                  <span className="text-sm font-medium text-zinc-700 whitespace-nowrap">{step}</span>
                </div>
                {i < workflow.length - 1 && (
                  <ArrowRight size={14} className="text-zinc-300 shrink-0 hidden sm:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6 bg-zinc-50/50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-zinc-900 text-center mb-3">Everything You Need</h2>
          <p className="text-zinc-500 text-center mb-12 max-w-lg mx-auto">
            Built with a modular architecture so every role gets exactly what they need.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f, i) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-zinc-200 p-6 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200"
              >
                <div className="p-2.5 bg-violet-50 rounded-lg w-fit mb-4">
                  <f.icon size={18} className="text-violet-600" />
                </div>
                <h3 className="font-semibold text-zinc-900 mb-1.5">{f.title}</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Roles */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-zinc-900 text-center mb-12">Four Dedicated Dashboards</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { role: 'Admin', desc: 'System-wide overview, user management, vendor approvals.', color: 'from-violet-500 to-violet-600' },
              { role: 'Procurement Officer', desc: 'Create RFQs, compare quotes, issue POs, generate invoices.', color: 'from-blue-500 to-blue-600' },
              { role: 'Manager', desc: 'Review and approve procurement workflows with full audit trail.', color: 'from-emerald-500 to-emerald-600' },
              { role: 'Vendor', desc: 'Submit quotations, track POs, view payments and RFQ invitations.', color: 'from-amber-500 to-amber-600' },
            ].map((r, i) => (
              <div key={i} className="relative overflow-hidden rounded-xl border border-zinc-200 p-6 bg-white">
                <div className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b ${r.color}`} />
                <h3 className="font-semibold text-zinc-900 mb-1 pl-3">{r.role}</h3>
                <p className="text-sm text-zinc-500 pl-3">{r.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 bg-zinc-900">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to streamline procurement?</h2>
          <p className="text-zinc-400 mb-8 max-w-lg mx-auto">
            Log in with your role-based credentials and explore the full ERP system.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="group px-8 py-3.5 text-sm font-medium text-zinc-900 bg-white hover:bg-zinc-100 rounded-xl transition-colors inline-flex items-center gap-2"
          >
            Sign In Now
            <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-zinc-100">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <span className="text-sm text-zinc-400">⬡ VendorBridge ERP</span>
          <span className="text-sm text-zinc-400">Built with Flask + React</span>
        </div>
      </footer>
    </div>
  )
}
