import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Eye, Download, Trash2, Search, Filter, Calendar } from 'lucide-react';
import { toast } from 'react-hot-toast';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Spinner from '../components/ui/Spinner';
import type { ContractHistoryItem, ContractHistoryResponse } from '../types';
import { apiService } from '../services/api';
import { formatDate, formatGasAmount, calculateGasSavings, downloadFile } from '@/lib/utils';

const ContractHistoryPage: React.FC = () => {
  const [contracts, setContracts] = useState<ContractHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedContract, setSelectedContract] = useState<ContractHistoryItem | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const pageSize = 10;
  const loadContracts = useCallback(async () => {
    try {
      setIsLoading(true);
      const response: ContractHistoryResponse = await apiService.getContractHistory(currentPage, pageSize);
      setContracts(response.contracts);
      setTotalPages(Math.ceil(response.total / pageSize));
      setError(null);    } catch (error: unknown) {
      const apiError = error as { detail?: string };
      setError(apiError.detail || 'Failed to load contract history');
      toast.error('Failed to load contract history');
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, pageSize]);

  useEffect(() => {
    loadContracts();
  }, [loadContracts]);

  const handleDeleteContract = async (contractId: string) => {
    if (!confirm('Are you sure you want to delete this contract?')) {
      return;
    }    try {
      await apiService.deleteContract(contractId);
      setContracts(contracts.filter(c => c.id !== contractId));
      toast.success('Contract deleted successfully');    } catch (error: unknown) {
      const apiError = error as { detail?: string };
      toast.error(apiError.detail || 'Failed to delete contract');
    }
  };

  const handleViewDetails = (contract: ContractHistoryItem) => {
    setSelectedContract(contract);
    setShowDetails(true);
  };

  const handleDownloadContract = (contract: ContractHistoryItem, type: 'original' | 'rewritten') => {
    const code = type === 'original' ? contract.original_contract : contract.rewritten_contract;
    const filename = `${contract.request_id}_${type}_contract.sol`;
    downloadFile(code, filename);
    toast.success(`${type === 'original' ? 'Original' : 'Rewritten'} contract downloaded`);
  };

  const filteredContracts = contracts.filter(contract =>
    contract.request_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.original_contract.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getOptimizationSummary = (contract: ContractHistoryItem) => {
    const gasSavings = calculateGasSavings(
      contract.rewrite_report.original_gas_estimate,
      contract.rewrite_report.optimized_gas_estimate
    );
    return {
      gasSavings: gasSavings.percentage,
      securityIssues: contract.analysis_report.security_issues.length,
      optimizations: contract.rewrite_report.optimization_techniques_applied.length
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
              Contract #{contract.request_id.slice(-8)}
            </h3>
            <p className="text-sm text-gray-600">
              {formatDate(contract.created_at)}
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

    const summary = getOptimizationSummary(selectedContract);

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
              <h2 className="text-2xl font-bold text-gray-900">
                Contract Details #{selectedContract.request_id.slice(-8)}
              </h2>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Gas Savings</p>
                  <p className="text-2xl font-bold text-green-600">
                    {summary.gasSavings.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatGasAmount(selectedContract.rewrite_report.original_gas_estimate)} → {formatGasAmount(selectedContract.rewrite_report.optimized_gas_estimate)}
                  </p>
                </div>
              </Card>

              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Security Score</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {selectedContract.analysis_report.gas_efficiency_score}%
                  </p>
                  <p className="text-xs text-gray-500">
                    {summary.securityIssues} issues found
                  </p>
                </div>
              </Card>

              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Quality Score</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {selectedContract.analysis_report.code_quality_metrics.complexity_score}%
                  </p>
                  <p className="text-xs text-gray-500">
                    Code complexity
                  </p>
                </div>
              </Card>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-3">Optimization Techniques Applied</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedContract.rewrite_report.optimization_techniques_applied.map((technique, index) => (
                    <span
                      key={index}
                      className="inline-flex px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-700"
                    >
                      {technique}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">Security Improvements</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedContract.rewrite_report.security_improvements.map((improvement, index) => (
                    <span
                      key={index}
                      className="inline-flex px-3 py-1 rounded-full text-sm bg-green-100 text-green-700"
                    >
                      {improvement}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex space-x-4">
                <Button
                  onClick={() => handleDownloadContract(selectedContract, 'original')}
                  variant="outline"
                  className="flex-1"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Original
                </Button>
                <Button
                  onClick={() => handleDownloadContract(selectedContract, 'rewritten')}
                  className="flex-1"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Optimized
                </Button>
              </div>
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
