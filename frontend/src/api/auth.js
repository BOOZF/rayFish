import service from './index'

// Hard-coded so the hosted site (no backend) can still be logged into.
// Public: anyone who reads this repo can see them.
const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = 'casella123'

export const login = async (username, password) => {
  try {
    return await service.post('/api/auth/login', { username, password }, { timeout: 5000 })
  } catch (err) {
    // A response means the backend answered, so its verdict stands
    if (err.response) throw err
    if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
      return { data: { token: 'offline-login' } }
    }
    throw Object.assign(new Error('Invalid username or password'), { response: { status: 401 } })
  }
}
