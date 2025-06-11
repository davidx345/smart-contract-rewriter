// API Response Types
export interface AnalysisReport {
  gas_efficiency_score: number
  security_issues: SecurityIssue[]
  optimization_suggestions: OptimizationSuggestion[]
  code_quality_metrics: CodeQualityMetrics
  vulnerability_assessment: VulnerabilityAssessment
}

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

export interface RewriteReport {
  original_gas_estimate: number
  optimized_gas_estimate: number
  gas_savings_percentage: number
  security_improvements: string[]
  optimization_techniques_applied: string[]
  code_quality_improvements: string[]
  compilation_status: CompilationStatus
  function_gas_analysis: GasFunctionAnalysis[]
}

export interface CompilationStatus {
  success: boolean
  compiler_version: string
  warnings: string[]
  errors: string[]
}

export interface GasFunctionAnalysis {
  function_name: string
  original_gas: number
  optimized_gas: number
  savings: number
  optimization_techniques: string[]
}

export interface ContractOutput {
  rewritten_code: string
  analysis_report: AnalysisReport
  rewrite_report: RewriteReport
  request_id: string
  processing_time: number
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
