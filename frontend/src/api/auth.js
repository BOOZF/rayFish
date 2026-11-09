import service from './index'

export const login = (username, password) =>
  service.post('/api/auth/login', { username, password })
