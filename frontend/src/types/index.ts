// API Response Types - Updated to match backend
export interface VulnerabilityInfo {
  type: string
  severity: string
  line_number?: number
  description: string
  recommendation: string
}

export interface GasFunctionAnalysis {
  function_name: string
  original_gas?: number
  optimized_gas?: number
  savings_absolute?: number
  savings_percentage?: number
}

export interface AnalysisReport {
  vulnerabilities: VulnerabilityInfo[]
  gas_analysis_per_function: GasFunctionAnalysis[]
  overall_code_quality_score?: number
  overall_security_score?: number
  general_suggestions: string[]
  estimated_total_gas_original?: number
  estimated_total_gas_optimized?: number
  total_gas_savings_absolute?: number
  total_gas_savings_percentage?: number
}

export interface GasOptimizationDetails {
  original_estimated_gas?: number | null
  optimized_estimated_gas?: number | null
  gas_saved?: number | null
  gas_savings_percentage?: number | null
}

export interface RewriteReport {
  // Fields used by RewriteDisplay.tsx and potentially by backend
  suggestions?: string[]
  gas_optimization_details?: GasOptimizationDetails | null
  security_improvements?: string[]

  // Original fields from backend schema - kept as optional 
  // if they might still be used or for other parts of app
  changes_summary?: string[]
  security_enhancements_made?: string[] // Consider if this is same as security_improvements
  readability_notes?: string
}

export interface ContractOutput {
  request_id: string
  original_code: string
  rewritten_code?: string
  analysis_report?: AnalysisReport
  rewrite_report?: RewriteReport
  compilation_success_original?: boolean
  compilation_success_rewritten?: boolean
  diff_summary?: string
  confidence_score?: number
  processing_time_seconds: number
  message: string
}

// Legacy types for backward compatibility (if needed)
export interface SecurityIssue {
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  category: string
  description: string
  line_number?: number
  recommendation: string
}

export interface OptimizationSuggestion {
  type: 'GAS_OPTIMIZATION' | 'SECURITY_IMPROVEMENT' | 'CODE_QUALITY' | 'PERFORMANCE'
  description: string
  impact: 'LOW' | 'MEDIUM' | 'HIGH'
  estimated_gas_savings?: number
  code_location?: string
}

export interface CodeQualityMetrics {
  complexity_score: number
  readability_score: number
  maintainability_score: number
  test_coverage_estimate: number
}

export interface VulnerabilityAssessment {
  overall_risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  detected_patterns: string[]
  recommendations: string[]
}

export interface CompilationStatus {
  success: boolean
  compiler_version: string
  warnings: string[]
  errors: string[]
}

export interface ContractHistoryItem {
  id: string
  original_contract: string
  rewritten_contract: string
  analysis_report: AnalysisReport
  rewrite_report: RewriteReport
  created_at: string
  request_id: string
}

export interface ContractHistoryResponse {
  contracts: ContractHistoryItem[]
  total: number
  page: number
  size: number
}

// API Request Types
export interface ContractInput {
  source_code: string
  contract_name?: string
  compiler_version?: string
}

export interface OptimizationRequest {
  source_code: string
  contract_name?: string
  compiler_version?: string
  optimization_goals: ('gas_efficiency' | 'security_hardening' | 'readability' | 'modularity' | 'upgradability' | 'storage_optimization' | 'transaction_speed')[]
  preserve_functionality: boolean
  target_solidity_version?: string
}

// UI State Types
export interface ContractState {
  originalCode: string
  rewrittenCode: string
  analysisReport: AnalysisReport | null
  rewriteReport: RewriteReport | null
  isAnalyzing: boolean
  isRewriting: boolean
  error: string | null
}

export interface HistoryState {
  contracts: ContractHistoryItem[]
  isLoading: boolean
  error: string | null
  pagination: {
    page: number
    size: number
    total: number
  }
}

// Component Props Types
export interface CodeEditorProps {
  value: string
  onChange: (value: string) => void
  language?: string
  readOnly?: boolean
  height?: string
}

export interface AnalysisCardProps {
  report: AnalysisReport
  className?: string
}

export interface RewriteCardProps {
  report: RewriteReport
  className?: string
}

export interface SecurityIssueItemProps {
  issue: SecurityIssue
}

export interface OptimizationSuggestionItemProps {
  suggestion: OptimizationSuggestion
}

// Form Types
export interface ContractForm {
  contract_code: string
  contract_name: string
  optimization_level: 'BASIC' | 'ADVANCED' | 'AGGRESSIVE'
  focus_areas: ('GAS_OPTIMIZATION' | 'SECURITY' | 'READABILITY' | 'BEST_PRACTICES')[]
  preserve_functionality: boolean
  target_solidity_version: string
}

// API Error Types
export interface ValidationError {
  type?: string
  loc?: string[]
  msg?: string
  input?: unknown
  url?: string
}

export interface APIError {
  detail: string | ValidationError[]
  status_code: number
}

// Toast Types
export type ToastType = 'success' | 'error' | 'warning' | 'info'
