import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Eye, Download, Trash2, Search, Filter, Calendar } from 'lucide-react';
import { toast } from 'react-hot-toast';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Spinner from '../components/ui/Spinner';
import type { ContractHistoryItem, ContractHistoryResponse, APIError, ValidationError } from '../types'; // Removed AnalysisReport, RewriteReport
import { apiService } from '../services/api';
import { formatDate, formatGasAmount, downloadFile } from '@/lib/utils';

const ContractHistoryPage: React.FC = () => {
  const [contracts, setContracts] = useState<ContractHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedContract, setSelectedContract] = useState<ContractHistoryItem | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const pageSize = 10; // This is now 'limit' for the API call
  const loadContracts = useCallback(async () => {
    try {
      setIsLoading(true);
      const response: ContractHistoryResponse = await apiService.getContractHistory(currentPage, pageSize);
      setContracts(response.contracts);
      setTotalPages(Math.ceil(response.total / pageSize));
      setError(null);
    } catch (error: unknown) {
      const apiError = error as APIError;
      const errorMessage = typeof apiError.detail === 'string' ? apiError.detail : (apiError.detail as ValidationError[]).map(d => d.msg).join(', ');
      setError(errorMessage || 'Failed to load contract history');
      toast.error(errorMessage || 'Failed to load contract history');
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, pageSize]); // pageSize is a dependency now

  useEffect(() => {
    loadContracts();
  }, [loadContracts]);

  const handleDeleteContract = async (contractId: string) => {
    if (!confirm('Are you sure you want to delete this contract?')) {
      return;
    }
    try {
      await apiService.deleteContract(contractId);
      setContracts(prevContracts => prevContracts.filter(c => c.id !== contractId));
      toast.success('Contract deleted successfully');
    } catch (error: unknown) {
      const apiError = error as APIError;
      const errorMessage = typeof apiError.detail === 'string' ? apiError.detail : (apiError.detail as ValidationError[]).map(d => d.msg).join(', ');
      toast.error(errorMessage || 'Failed to delete contract');
    }
  };

  const handleViewDetails = (contract: ContractHistoryItem) => {
    setSelectedContract(contract);
    setShowDetails(true);
  };

  const handleDownloadContract = (contract: ContractHistoryItem, type: 'original' | 'rewritten') => {
    // Safely access potentially undefined properties
    const code = type === 'original' ? contract.original_contract : contract.rewritten_contract;
    if (!code) {
      toast.error(`No ${type} code available for this contract.`);
      return;
    }
    const filename = `${contract.contract_name || contract.id}_${type}_contract.sol`; // Use contract.contract_name or contract.id for filename
    downloadFile(code, filename);
    toast.success(`${type === 'original' ? 'Original' : 'Rewritten'} contract downloaded`);
  };

  const filteredContracts = contracts.filter(contract =>
    contract.id.toLowerCase().includes(searchTerm.toLowerCase()) || // Search by ID
    (contract.contract_name && contract.contract_name.toLowerCase().includes(searchTerm.toLowerCase())) || // Search by contract name
    (contract.original_contract && contract.original_contract.toLowerCase().includes(searchTerm.toLowerCase())) // Corrected: use original_contract
  );

  const getOptimizationSummary = (contract: ContractHistoryItem) => {
    // Safe navigation for potentially undefined reports or nested properties
    const gasSavingsPercentage = contract.rewrite_report?.gas_optimization_details?.gas_savings_percentage;
    const securityIssuesCount = contract.analysis_report?.vulnerabilities?.length ?? 0;
    const optimizationsAppliedCount = contract.rewrite_report?.suggestions?.length ?? 0; // Or another relevant field

    return {
      gasSavings: typeof gasSavingsPercentage === 'number' ? gasSavingsPercentage : 0,
      securityIssues: securityIssuesCount,
      optimizations: optimizationsAppliedCount
    };
  };

  const ContractCard: React.FC<{ contract: ContractHistoryItem }> = ({ contract }) => {
    const summary = getOptimizationSummary(contract);
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card hover:shadow-xl transition-shadow duration-300"
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {/* Display contract name if available, otherwise fallback to ID */}
              {contract.contract_name || `Contract #${contract.id.slice(-8)}`}
            </h3>
            <p className="text-sm text-gray-600">
              {formatDate(contract.created_at)} {/* Corrected: use contract.created_at */}
            </p>
          </div>
          <div className="flex space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleViewDetails(contract)}
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDeleteContract(contract.id)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <p className="text-sm text-gray-600">Gas Savings</p>
            <p className="text-lg font-bold text-green-600">
              {summary.gasSavings.toFixed(1)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Security Issues</p>
            <p className="text-lg font-bold text-orange-600">
              {summary.securityIssues}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Optimizations</p>
            <p className="text-lg font-bold text-blue-600">
              {summary.optimizations}
            </p>
          </div>
        </div>

        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownloadContract(contract, 'original')}
            className="flex-1"
          >
            <Download className="h-4 w-4 mr-1" />
            Original
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownloadContract(contract, 'rewritten')}
            className="flex-1"
          >
            <Download className="h-4 w-4 mr-1" />
            Optimized
          </Button>
        </div>
      </motion.div>
    );
  };

  const ContractDetailsModal: React.FC = () => {
    if (!selectedContract) return null;

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={() => setShowDetails(false)}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-800">
                {selectedContract.contract_name || `Contract Details (${selectedContract.id.slice(-8)})`}
              </h2>
              {/* Changed size="icon" to size="sm" */}
              <Button variant="ghost" size="sm" onClick={() => setShowDetails(false)}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <Card className="p-4">
                <h3 className="font-semibold text-gray-700 mb-2">Summary</h3>
                <p className="text-sm text-gray-600">Processed: {formatDate(selectedContract.created_at)}</p>
                <p className="text-sm text-gray-600">Request ID: {selectedContract.request_id}</p>
                {selectedContract.analysis_report?.overall_code_quality_score !== undefined && selectedContract.analysis_report?.overall_code_quality_score !== null && (
                  <p className="text-sm text-gray-600">Code Quality Score: {(selectedContract.analysis_report.overall_code_quality_score).toFixed(1)}%</p>
                )}
                {selectedContract.analysis_report?.overall_security_score !== undefined && selectedContract.analysis_report?.overall_security_score !== null && (
                  <p className="text-sm text-gray-600">Security Score: {(selectedContract.analysis_report.overall_security_score).toFixed(1)}%</p>
                )}
              </Card>
              <Card className="p-4">
                <h3 className="font-semibold text-gray-700 mb-2">Gas Optimization</h3>
                {selectedContract.rewrite_report?.gas_optimization_details ? (
                  <>
                    <p className="text-sm text-gray-600">
                      Original Gas: {formatGasAmount(selectedContract.rewrite_report.gas_optimization_details.original_estimated_gas ?? 0)}
                    </p>
                    <p className="text-sm text-gray-600">
                      Optimized Gas: {formatGasAmount(selectedContract.rewrite_report.gas_optimization_details.optimized_estimated_gas ?? 0)}
                    </p>
                    <p className="text-sm text-green-600 font-semibold">
                      Savings: {(selectedContract.rewrite_report.gas_optimization_details.gas_savings_percentage ?? 0).toFixed(1)}%
                      ({formatGasAmount(selectedContract.rewrite_report.gas_optimization_details.gas_saved ?? 0)})
                    </p>
                  </>
                ) : <p className="text-sm text-gray-500">No gas optimization details available.</p>}
              </Card>
            </div>

            {/* Analysis Report Details */}
            {selectedContract.analysis_report && (
              <Card className="p-4 mb-6">
                <h3 className="font-semibold text-gray-700 mb-3">Analysis Report</h3>
                <div className="space-y-3">
                  <div>
                    <h4 className="text-md font-medium text-gray-600 mb-1">Vulnerabilities ({selectedContract.analysis_report.vulnerabilities?.length || 0})</h4>
                    {selectedContract.analysis_report.vulnerabilities?.length > 0 ? (
                      <ul className="list-disc list-inside text-sm text-gray-600 pl-4">
                        {selectedContract.analysis_report.vulnerabilities.map((vuln, index: number) => (
                          <li key={index} className="mb-1">
                            <span className={`font-semibold ${vuln.severity === 'HIGH' || vuln.severity === 'CRITICAL' ? 'text-red-600' : vuln.severity === 'MEDIUM' ? 'text-yellow-600' : 'text-green-600'}`}>
                              {vuln.type} ({vuln.severity})
                            </span>
                            {vuln.line_number && ` - Line ${vuln.line_number}`}: {vuln.description}
                          </li>
                        ))}
                      </ul>
                    ) : <p className="text-sm text-gray-500">No vulnerabilities detected.</p>}
                  </div>
                  <div>
                    <h4 className="text-md font-medium text-gray-600 mb-1">Gas Analysis per Function</h4>
                    {selectedContract.analysis_report.gas_analysis_per_function?.length > 0 ? (
                      <ul className="list-disc list-inside text-sm text-gray-600 pl-4">
                        {selectedContract.analysis_report.gas_analysis_per_function.map((gas, index: number) => (
                          <li key={index}>
                            {gas.function_name}: Original: {formatGasAmount(gas.original_gas ?? 0)}, Optimized: {formatGasAmount(gas.optimized_gas ?? 0)} (Savings: {(gas.savings_percentage ?? 0).toFixed(1)}%)
                          </li>
                        ))}
                      </ul>
                    ) : <p className="text-sm text-gray-500">No per-function gas analysis available.</p>}
                  </div>
                  {selectedContract.analysis_report.general_suggestions?.length > 0 && (
                    <div>
                      <h4 className="text-md font-medium text-gray-600 mb-1">General Suggestions</h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 pl-4">
                        {selectedContract.analysis_report.general_suggestions.map((suggestion: string, index: number) => (
                          <li key={index}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Rewrite Report Details */}
            {selectedContract.rewrite_report && (
              <Card className="p-4 mb-6">
                <h3 className="font-semibold text-gray-700 mb-3">Rewrite Report</h3>
                <div className="space-y-3">
                  {selectedContract.rewrite_report.suggestions && selectedContract.rewrite_report.suggestions.length > 0 && (
                    <div>
                      <h4 className="text-md font-medium text-gray-600 mb-1">Suggestions Applied ({selectedContract.rewrite_report.suggestions.length})</h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 pl-4">
                        {selectedContract.rewrite_report.suggestions.map((suggestion: string, index: number) => (
                          <li key={index}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedContract.rewrite_report.security_improvements && selectedContract.rewrite_report.security_improvements.length > 0 && (
                    <div>
                      <h4 className="text-md font-medium text-gray-600 mb-1">Security Improvements ({selectedContract.rewrite_report.security_improvements.length})</h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 pl-4">
                        {selectedContract.rewrite_report.security_improvements.map((improvement: string, index: number) => (
                          <li key={index}>{improvement}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                   {selectedContract.rewrite_report.changes_summary && selectedContract.rewrite_report.changes_summary.length > 0 && (
                    <div>
                      <h4 className="text-md font-medium text-gray-600 mb-1">Changes Summary</h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 pl-4">
                        {selectedContract.rewrite_report.changes_summary.map((change: string, index: number) => (
                          <li key={index}>{change}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedContract.rewrite_report.readability_notes && (
                     <div>
                      <h4 className="text-md font-medium text-gray-600 mb-1">Readability Notes</h4>
                      <p className="text-sm text-gray-600">{selectedContract.rewrite_report.readability_notes}</p>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Code Diff View (Placeholder or simplified) */}
            <Card className="p-4">
              <h3 className="font-semibold text-gray-700 mb-2">Code Versions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-md font-medium text-gray-600 mb-1">Original Code</h4>
                  <pre className="bg-gray-100 p-3 rounded-md text-xs overflow-auto max-h-60">
                    <code>{selectedContract.original_contract}</code>
                  </pre>
                  {/* Changed variant="link" to variant="ghost" */}
                  <Button 
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDownloadContract(selectedContract, 'original')}
                    className="mt-2"
                  >
                    Download Original
                  </Button>
                </div>
                <div>
                  <h4 className="text-md font-medium text-gray-600 mb-1">Rewritten Code</h4>
                  {selectedContract.rewritten_contract ? (
                    <>
                      <pre className="bg-gray-100 p-3 rounded-md text-xs overflow-auto max-h-60">
                        <code>{selectedContract.rewritten_contract}</code>
                      </pre>
                      {/* Changed variant="link" to variant="ghost" */}
                      <Button 
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownloadContract(selectedContract, 'rewritten')}
                        className="mt-2"
                      >
                        Download Rewritten
                      </Button>
                    </>
                  ) : <p className="text-sm text-gray-500">No rewritten code available.</p>}
                </div>
              </div>
            </Card>

            <div className="mt-6 flex justify-end">
              <Button onClick={() => setShowDetails(false)}>Close</Button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Contract History</h1>
          <p className="text-gray-600">View and manage your analyzed smart contracts</p>
        </div>

        {/* Filters and Search */}
        <Card className="mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by contract ID or code..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            <div className="flex space-x-2">
              <Button variant="outline">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
              <Button variant="outline" onClick={loadContracts}>
                <Search className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </Card>

        {/* Content */}
        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <Spinner size="lg" />
          </div>
        ) : error ? (
          <Card className="text-center py-12">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={loadContracts} variant="outline">
              Try Again
            </Button>
          </Card>
        ) : filteredContracts.length === 0 ? (
          <Card className="text-center py-12">
            <Calendar className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No contracts found</h3>
            <p className="text-gray-600">
              {searchTerm ? 'No contracts match your search criteria.' : 'You haven\'t analyzed any contracts yet.'}
            </p>
          </Card>
        ) : (
          <>
            {/* Contracts Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {filteredContracts.map((contract) => (
                <ContractCard key={contract.id} contract={contract} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center space-x-2">
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                
                <span className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </span>
                
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}

        {/* Contract Details Modal */}
        {showDetails && <ContractDetailsModal />}
      </div>
    </div>
  );
};

export default ContractHistoryPage;
