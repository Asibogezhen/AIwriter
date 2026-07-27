import request from './request'

export const vipApi = {
  status: () => request.get('/v1/vip/status'),
  redeem: (code: string) => request.post('/v1/vip/redeem', { code }),
  pricing: () => request.get('/v1/vip/pricing'),
  createOrder: (planType: string) => request.post('/v1/vip/orders', { plan_type: planType }),
  payOrder: (orderNo: string) => request.post(`/v1/vip/orders/${orderNo}/pay`),
}

export const adminApi = {
  generateCodes: (count: number, batch: string, note: string) =>
    request.post('/v1/admin/codes/generate', { count, batch, note }),
  listCodes: (page: number, batch: string) =>
    request.get('/v1/admin/codes', { page, page_size: 20, batch }),
  stats: () => request.get('/v1/admin/stats'),
}
