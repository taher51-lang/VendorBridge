import api from './api'

export const analyticsApi = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getActivityLogs: (params) => api.get('/analytics/activity-logs', { params }),
  getSpendByCategory: (params) => api.get('/analytics/spend-by-category', { params }),
  getSpendByVendor: (params) => api.get('/analytics/spend-by-vendor', { params }),
  getVendorPerformance: () => api.get('/analytics/vendor-performance'),
  getMonthlyTrends: () => api.get('/analytics/monthly-trends'),
}
