import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiService } from '../services/api'
import type { ContractInput, OptimizationRequest, APIError } from '../types'
import toast from 'react-hot-toast'

// Query keys
export const QUERY_KEYS = {
  health: ['health'],
  contractHistory: ['contracts', 'history'],
  contract: (id: string) => ['contracts', id],
} as const

// Health check hook
export function useHealthCheck() {
  return useQuery({
    queryKey: QUERY_KEYS.health,
    queryFn: apiService.healthCheck,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
  })
}

// Contract analysis hook
export function useAnalyzeContract() {
  return useMutation({
    mutationFn: (input: ContractInput) => apiService.analyzeContract(input),
    onSuccess: () => {
      toast.success('Contract analysis completed successfully!')
    },    onError: (error: APIError) => {
      toast.error(`Analysis failed: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Contract rewrite hook
export function useRewriteContract() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: OptimizationRequest) => apiService.rewriteContract(request),
    onSuccess: () => {
      toast.success('Contract rewrite completed successfully!')
      // Invalidate history to show new contract
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.contractHistory })
    },    onError: (error: APIError) => {
      toast.error(`Rewrite failed: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Contract history hook
export function useContractHistory(page: number = 1, size: number = 10) {
  return useQuery({
    queryKey: [...QUERY_KEYS.contractHistory, page, size],
    queryFn: () => apiService.getContractHistory(page, size),
    staleTime: 30 * 1000, // 30 seconds
  })
}

// Single contract hook
export function useContract(contractId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.contract(contractId),
    queryFn: () => apiService.getContractById(contractId),
    enabled: !!contractId,
  })
}

// Delete contract hook
export function useDeleteContract() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (contractId: string) => apiService.deleteContract(contractId),
    onSuccess: () => {
      toast.success('Contract deleted successfully!')
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.contractHistory })
    },    onError: (error: APIError) => {
      toast.error(`Delete failed: ${error.detail || 'Unknown error'}`)
    },
  })
}
