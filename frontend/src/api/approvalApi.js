import api from './api'

export const approvalApi = {
  getAll: (params) => api.get('/approvals/', { params }),
  getOne: (id) => api.get(`/approvals/${id}`),
  getPending: () => api.get('/approvals/pending'),
  initiate: (data) => api.post('/approvals/', data),
  action: (id, data) => api.post(`/approvals/${id}/action`, data),
  cancel: (id) => api.post(`/approvals/${id}/cancel`),
}
