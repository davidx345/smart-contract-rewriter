import axios, { AxiosError } from 'axios'
import type { AxiosInstance } from 'axios'
import type {
  ContractInput,
  OptimizationRequest,
  ContractOutput,
  ContractHistoryResponse,
  APIError,
} from '../types'

class APIService {
  private api: AxiosInstance

  constructor() {
    // Ensure VITE_API_BASE_URL is correctly used, and the fallback is to the /api/v1 path
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'https://smart-contract-rewriter-backend.onrender.com/api/v1';
    this.api = axios.create({
      baseURL: baseURL.endsWith('/api/v1') ? baseURL : `${baseURL}/api/v1`, // Ensure /api/v1 is present
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
        // Ensure errorData can be an array for validation errors or an object for other errors
        const errorData = error.response?.data as { detail?: string | Array<{ msg: string, loc: string[], type: string }> } | undefined;
        let errorMessage: string = 'An error occurred';

        if (typeof errorData?.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData?.detail)) {
          // Handle Pydantic validation errors
          errorMessage = errorData.detail.map((err: { msg: string }) => err.msg).join(', ');
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        const apiError: APIError = {
          detail: errorMessage,
          status_code: error.response?.status || 500
        }
        return Promise.reject(apiError)
      }
    )
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    // Adjust health check endpoint if it's not under /api/v1
    const healthBaseURL = import.meta.env.VITE_API_BASE_URL || 'https://smart-contract-rewriter-backend.onrender.com';
    const healthApi = axios.create({ baseURL: healthBaseURL });
    const response = await healthApi.get('/health');
    return response.data;
  }
  // Analyze contract
  async analyzeContract(contractInput: ContractInput): Promise<ContractOutput> {
    const response = await this.api.post('/contracts/analyze', contractInput) // Removed /api/v1 as it's in baseURL
    return response.data
  }

  // Rewrite contract
  async rewriteContract(optimizationRequest: OptimizationRequest): Promise<ContractOutput> {
    const response = await this.api.post('/contracts/rewrite', optimizationRequest) // Removed /api/v1
    return response.data
  }  // Get contract history
  async getContractHistory(page: number = 1, limit: number = 10): Promise<ContractHistoryResponse> {
    const skip = (page - 1) * limit;
    const response = await this.api.get('/contracts/history', {
      params: { skip, limit }
    })
    
    // The API returns an array directly, transform it to match our interface
    const contracts = Array.isArray(response.data) ? response.data.map((item: any) => ({
      ...item,
      // Ensure timestamp is in string format for frontend
      timestamp: typeof item.timestamp === 'string' ? item.timestamp : new Date(item.timestamp).toISOString(),
      created_at: typeof item.timestamp === 'string' ? item.timestamp : new Date(item.timestamp).toISOString(),
      details: {
        ...item.details,
        // Ensure proper structure for frontend consumption
        analysis_report: item.details?.analysis_report,
        rewrite_report: item.details?.rewrite_summary ? {
          suggestions: item.details.rewrite_summary?.changes_summary || [],
          gas_optimization_details: {
            gas_savings_percentage: item.details.gas_savings_percentage || 0
          },
          security_improvements: item.details.rewrite_summary?.security_enhancements_made || [],
          rewritten_code: item.details?.rewritten_code
        } : undefined,
        original_code: item.details?.original_code,
        rewritten_code: item.details?.rewritten_code,
        vulnerabilities_count: item.details?.vulnerabilities_count || 0,
        gas_savings_percentage: item.details?.gas_savings_percentage || 0,
        changes_count: item.details?.changes_count || 0
      }
    })) : [];
    
    return {
      contracts,
      total: contracts.length, // Since we don't have total from API, use array length
      page,
      size: limit
    }
  }

  // Get specific contract by ID
  async getContractById(contractId: string): Promise<ContractOutput> {
    const response = await this.api.get(`/contracts/${contractId}`) // Removed /api/v1
    return response.data
  }

  // Delete contract from history
  async deleteContract(contractId: string): Promise<void> {
    await this.api.delete(`/contracts/${contractId}`) // Removed /api/v1
  }
}

export const apiService = new APIService()
export default apiService
