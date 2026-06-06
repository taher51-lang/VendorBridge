import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/analyticsApi'
import { BarChart2, TrendingUp, Building2, PieChart } from 'lucide-react'
import useAuthStore from '../store/authStore'

function MetricCard({ title, children, icon: Icon, className = '' }) {
  return (
    <div className={`bg-white rounded-xl border border-zinc-200 overflow-hidden ${className}`}>
      <div className="px-5 py-4 border-b border-zinc-100 flex items-center gap-2">
        {Icon && <Icon size={15} className="text-zinc-400" />}
        <h3 className="text-sm font-semibold text-zinc-900">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  )
}

function BarChart({ data, labelKey, valueKey, maxValue }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-zinc-400 text-center py-4">No data available</p>
  }
  const max = maxValue || Math.max(...data.map(d => Number(d[valueKey]) || 0), 1)

  return (
    <div className="space-y-3">
      {data.map((item, i) => {
        const val = Number(item[valueKey]) || 0
        const pct = Math.max((val / max) * 100, 2)
        return (
          <div key={i}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-zinc-700 font-medium truncate max-w-[200px]">{item[labelKey]}</span>
              <span className="text-zinc-500 font-medium">₹{val.toLocaleString('en-IN')}</span>
            </div>
            <div className="h-2.5 bg-zinc-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 to-blue-500 transition-all duration-700"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function PerformanceTable({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-zinc-400 text-center py-4">No vendor data available</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-zinc-500 border-b border-zinc-100">
            <th className="pb-2 font-medium">Vendor</th>
            <th className="pb-2 font-medium text-center">Rating</th>
            <th className="pb-2 font-medium text-center">POs</th>
            <th className="pb-2 font-medium text-center">Fulfillment</th>
            <th className="pb-2 font-medium text-right">Spend</th>
          </tr>
        </thead>
        <tbody>
          {data.map((v, i) => (
            <tr key={i} className="border-b border-zinc-50">
              <td className="py-2.5 font-medium text-zinc-800 max-w-[200px] truncate">{v.vendor_name}</td>
              <td className="py-2.5 text-center">
                <div className="flex items-center justify-center gap-1">
                  <span className="text-amber-500">★</span>
                  <span className="text-zinc-700">{Number(v.avg_rating || 0).toFixed(1)}</span>
                </div>
              </td>
              <td className="py-2.5 text-center text-zinc-600">{v.total_pos}</td>
              <td className="py-2.5 text-center">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  v.fulfillment_rate >= 80
                    ? 'bg-emerald-100 text-emerald-700'
                    : v.fulfillment_rate >= 50
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-rose-100 text-rose-700'
                }`}>
                  {v.fulfillment_rate}%
                </span>
              </td>
              <td className="py-2.5 text-right text-zinc-700 font-medium">
                ₹{Number(v.total_spend || 0).toLocaleString('en-IN')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MonthlyTrendChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-zinc-400 text-center py-4">No monthly data available</p>
  }

  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const maxSpend = Math.max(...data.map(d => Number(d.total_spend)), 1)

  return (
    <div className="flex items-end gap-2 h-40">
      {data.slice(-12).map((item, i) => {
        const height = Math.max((Number(item.total_spend) / maxSpend) * 100, 4)
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-[10px] text-zinc-400">{item.po_count}</span>
            <div className="w-full relative group">
              <div
                className="w-full bg-gradient-to-t from-violet-500 to-violet-400 rounded-t transition-all duration-500 hover:from-violet-600 hover:to-violet-500 cursor-pointer"
                style={{ height: `${height}px` }}
              >
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-zinc-800 text-white text-[10px] px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  ₹{Number(item.total_spend).toLocaleString('en-IN')}
                </div>
              </div>
            </div>
            <span className="text-[10px] text-zinc-400">{months[item.month - 1]}</span>
          </div>
        )
      })}
    </div>
  )
}

export default function Reports() {
  const { user } = useAuthStore()
  const isVendor = user?.role === 'vendor'

  const { data: spendByCategory, isLoading: loadingCategory } = useQuery({
    queryKey: ['spend-by-category'],
    queryFn: () => analyticsApi.getSpendByCategory().then(r => r.data?.data),
    enabled: !isVendor,
  })

  const { data: spendByVendor, isLoading: loadingVendor } = useQuery({
    queryKey: ['spend-by-vendor'],
    queryFn: () => analyticsApi.getSpendByVendor({ limit: 10 }).then(r => r.data?.data),
    enabled: !isVendor,
  })

  const { data: performance, isLoading: loadingPerf } = useQuery({
    queryKey: ['vendor-performance'],
    queryFn: () => analyticsApi.getVendorPerformance().then(r => r.data?.data),
    enabled: !isVendor,
  })

  const { data: monthlyTrends, isLoading: loadingTrends } = useQuery({
    queryKey: ['monthly-trends'],
    queryFn: () => analyticsApi.getMonthlyTrends().then(r => r.data?.data),
    enabled: !isVendor,
  })

  if (isVendor) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2">
            <BarChart2 size={22} className="text-violet-500" />
            Reports
          </h1>
        </div>
        <div className="bg-white rounded-xl border border-zinc-200 py-16 text-center">
          <BarChart2 size={40} className="mx-auto text-zinc-300 mb-3" />
          <p className="text-zinc-500 text-sm">Reports are available for procurement officers and managers.</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2">
          <BarChart2 size={22} className="text-violet-500" />
          Reports & Analytics
        </h1>
        <p className="text-zinc-500 text-sm mt-1">
          Procurement spending, vendor performance, and trends.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <MetricCard title="Spend by Category" icon={PieChart}>
          {loadingCategory ? (
            <div className="space-y-3 animate-pulse">
              {[...Array(3)].map((_, i) => <div key={i} className="h-8 bg-zinc-50 rounded" />)}
            </div>
          ) : (
            <BarChart data={spendByCategory} labelKey="category_name" valueKey="total_spend" />
          )}
        </MetricCard>

        <MetricCard title="Top Vendors by Spend" icon={Building2}>
          {loadingVendor ? (
            <div className="space-y-3 animate-pulse">
              {[...Array(3)].map((_, i) => <div key={i} className="h-8 bg-zinc-50 rounded" />)}
            </div>
          ) : (
            <BarChart data={spendByVendor} labelKey="vendor_name" valueKey="total_spend" />
          )}
        </MetricCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <MetricCard title="Monthly Procurement Trends" icon={TrendingUp}>
          {loadingTrends ? (
            <div className="h-40 bg-zinc-50 rounded animate-pulse" />
          ) : (
            <MonthlyTrendChart data={monthlyTrends} />
          )}
        </MetricCard>

        <MetricCard title="Vendor Performance" icon={Building2}>
          {loadingPerf ? (
            <div className="space-y-3 animate-pulse">
              {[...Array(3)].map((_, i) => <div key={i} className="h-10 bg-zinc-50 rounded" />)}
            </div>
          ) : (
            <PerformanceTable data={performance} />
          )}
        </MetricCard>
      </div>
    </div>
  )
}
