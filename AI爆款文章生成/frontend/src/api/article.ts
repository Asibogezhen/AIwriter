import request from './request'

export interface GenerateParams {
  topic: string
  style?: string
  wordCount?: number
  imagePreference?: string
  // 小红书平台
  platform?: string
  xhsCategory?: string
  xhsPersona?: string
  xhsImageStyle?: string
  // 产品信息
  productName?: string
  productDescription?: string
}

export const articleApi = {
  generate: (params: GenerateParams) =>
    request.post<{ articleId: string }>('/v1/articles/generate', params),

  list: (page = 1, pageSize = 10) =>
    request.get('/v1/articles', { page, page_size: pageSize }),

  detail: (id: string) =>
    request.get(`/v1/articles/${id}`),

  delete: (id: string) =>
    request.delete(`/v1/articles/${id}`),
}
