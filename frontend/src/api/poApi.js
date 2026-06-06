import api from './api'

export const poApi = {
  getAll: (params) => api.get('/purchase-orders/', { params }),
  getOne: (id) => api.get(`/purchase-orders/${id}`),
  create: (data) => api.post('/purchase-orders/', data),
  update: (id, data) => api.put(`/purchase-orders/${id}`, data),
  acknowledge: (id) => api.post(`/purchase-orders/${id}/acknowledge`),
  fulfill: (id) => api.post(`/purchase-orders/${id}/fulfill`),
  cancel: (id, reason) => api.post(`/purchase-orders/${id}/cancel`, { reason }),
}
