import api from './api'

export const vendorApi = {
  getAll: (params) => api.get('/vendors/', { params }),
  getOne: (id) => api.get(`/vendors/${id}`),
  update: (id, data) => api.put(`/vendors/${id}`, data),
  approve: (id) => api.post(`/vendors/${id}/approve`),
  suspend: (id, reason) => api.post(`/vendors/${id}/suspend`, { reason }),
  blacklist: (id, reason) => api.post(`/vendors/${id}/blacklist`, { reason }),
  getRatings: (id, params) => api.get(`/vendors/${id}/ratings`, { params }),
  rateVendor: (id, data) => api.post(`/vendors/${id}/ratings`, data),
  getCategories: () => api.get('/vendors/categories'),
  createCategory: (data) => api.post('/vendors/categories', data),
}
