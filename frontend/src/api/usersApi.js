import api from './api'

export const usersApi = {
  getAll: (params) => api.get('/users/', { params }),
  create: (data) => api.post('/auth/register', data),
  deactivate: (id) => api.patch(`/users/${id}/deactivate`),
  activate: (id) => api.patch(`/users/${id}/activate`),
  delete: (id) => api.delete(`/users/${id}`),
}
