import api from './api'

export const invoiceApi = {
  getAll: (params) => api.get('/invoices/', { params }),
  getOne: (id) => api.get(`/invoices/${id}`),
  create: (data) => api.post('/invoices/', data),
  update: (id, data) => api.put(`/invoices/${id}`, data),
  generatePdf: (id) => api.post(`/invoices/${id}/pdf`, {}, { responseType: 'blob' }),
  send: (id, data) => api.post(`/invoices/${id}/send`, data),
  markPaid: (id) => api.post(`/invoices/${id}/mark-paid`),
  cancel: (id) => api.post(`/invoices/${id}/cancel`),
}
