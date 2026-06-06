import api from './api'

export const quotationApi = {
  getAll: (params) => api.get('/quotations/', { params }),
  getOne: (id) => api.get(`/quotations/${id}`),
  create: (data) => api.post('/quotations/', data),
  update: (id, data) => api.put(`/quotations/${id}`, data),
  submit: (id) => api.post(`/quotations/${id}/submit`),
  select: (id) => api.post(`/quotations/${id}/select`),
  compare: (rfqId) => api.get(`/quotations/compare/${rfqId}`),
}
