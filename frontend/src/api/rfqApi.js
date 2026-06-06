import api from './api'

export const rfqApi = {
  getAll: (params) => api.get('/rfqs/', { params }),
  getOne: (id) => api.get(`/rfqs/${id}`),
  create: (data) => api.post('/rfqs/', data),
  update: (id, data) => api.put(`/rfqs/${id}`, data),
  publish: (id) => api.post(`/rfqs/${id}/publish`),
  close: (id) => api.post(`/rfqs/${id}/close`),
  cancel: (id) => api.post(`/rfqs/${id}/cancel`),
  inviteVendors: (id, data) => api.post(`/rfqs/${id}/invite-vendors`, data),
}
