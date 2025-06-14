import axios, { AxiosError } from 'axios'
import type { AxiosInstance } from 'axios'
import type {
  ContractInput,
  OptimizationRequest,
  ContractOutput,
  ContractHistoryResponse,
  APIError
} from '../types'

class APIService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const errorData = error.response?.data as { detail?: string } | undefined
        const apiError: APIError = {
          detail: errorData?.detail || error.message || 'An error occurred',
          status_code: error.response?.status || 500
        }
        return Promise.reject(apiError)
      }
    )
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.api.get('/health')
    return response.data
  }
  // Analyze contract
  async analyzeContract(contractInput: ContractInput): Promise<ContractOutput> {
    const response = await this.api.post('/api/v1/contracts/analyze', contractInput)
    return response.data
  }

  // Rewrite contract
  async rewriteContract(optimizationRequest: OptimizationRequest): Promise<ContractOutput> {
    const response = await this.api.post('/api/v1/contracts/rewrite', optimizationRequest)
    return response.data
  }

  // Get contract history
  async getContractHistory(page: number = 1, size: number = 10): Promise<ContractHistoryResponse> {
    const response = await this.api.get('/api/v1/contracts/history', {
      params: { page, size }
    })
    return response.data
  }

  // Get specific contract by ID
  async getContractById(contractId: string): Promise<ContractOutput> {
    const response = await this.api.get(`/api/v1/contracts/${contractId}`)
    return response.data
  }

  // Delete contract from history
  async deleteContract(contractId: string): Promise<void> {
    await this.api.delete(`/api/v1/contracts/${contractId}`)
  }
}

export const apiService = new APIService()
export default apiService
