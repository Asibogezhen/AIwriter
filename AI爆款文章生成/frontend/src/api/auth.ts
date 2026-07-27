import request from './request'

export const authApi = {
  login: (email: string, password: string) =>
    request.post('/v1/auth/login', { email, password }),

  register: (email: string, password: string, nickname: string) =>
    request.post('/v1/auth/register', { email, password, nickname }),

  me: () => request.get('/v1/auth/me'),
}
