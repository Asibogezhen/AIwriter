import axios from 'axios'
import { message } from 'ant-design-vue'

const http = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    const { code, message: msg, data } = response.data
    if (code !== 0) {
      if (code === 10401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      message.error(msg || '请求失败')
      return Promise.reject(new Error(msg))
    }
    // 将响应数据替换为业务 data 字段
    response.data = data
    return response
  },
  (error) => {
    message.error(error.message || '网络错误')
    return Promise.reject(error)
  },
)

// 封装方法，自动提取 response.data
async function get<T = any>(url: string, params?: any): Promise<T> {
  const res = await http.get(url, { params })
  return res.data as T
}

async function post<T = any>(url: string, data?: any): Promise<T> {
  const res = await http.post(url, data)
  return res.data as T
}

async function del<T = any>(url: string): Promise<T> {
  const res = await http.delete(url)
  return res.data as T
}

export default { get, post, delete: del }
