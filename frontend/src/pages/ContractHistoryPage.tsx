import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Eye, Download, Trash2, Search, Calendar, X } from 'lucide-react'; // Removed Filter
import { toast } from 'react-hot-toast';
// import Card from '../components/ui/Card'; // Removed Card import
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Spinner from '../components/ui/Spinner';
import AnalysisDisplay from '../components/contract/AnalysisDisplay';
import RewriteDisplay from '../components/contract/RewriteDisplay';
import type { ContractHistoryItem, ContractHistoryResponse, APIError, ValidationError, ContractHistoryItemDetails } from '../types';
import { apiService } from '../services/api';
import { formatDate } from '../lib/utils';

const ContractHistoryPage: React.FC = () => {
  const [contracts, setContracts] = useState<ContractHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  // const [_filterCriteria, _setFilterCriteria] = useState<keyof ContractHistoryItem['details'] | 'all'>('all'); // Marked as unused for now
  // const [_sortOrder, _setSortOrder] = useState<'asc' | 'desc'>('desc'); // Marked as unused for now
  const [selectedContractDetails, setSelectedContractDetails] = useState<ContractHistoryItemDetails | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 10; // Or make this configurable
  const loadContracts = useCallback(async () => {
    try {
      setIsLoading(true);
      const response: ContractHistoryResponse = await apiService.getContractHistory(currentPage, pageSize);
      // Ensure contracts is always an array
      const contractsArray = Array.isArray(response.contracts) ? response.contracts : [];
      setContracts(contractsArray);
      setTotalPages(Math.ceil((response.total || contractsArray.length) / pageSize));
      setError(null);
    } catch (error: unknown) {
      console.error('Error loading contracts:', error);
      const apiError = error as APIError;
      const errorMessage = typeof apiError.detail === 'string' ? apiError.detail : 
                          Array.isArray(apiError.detail) ? (apiError.detail as ValidationError[]).map(d => d.msg).join(', ') :
                          'Failed to load contract history';
      setError(errorMessage);
      toast.error(errorMessage);
      // Set empty array on error to prevent filter errors
      setContracts([]);
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
    }
    try {
      await apiService.deleteContract(contractId);
      setContracts(prevContracts => (prevContracts || []).filter(c => c.id !== contractId));
      toast.success('Contract deleted successfully');
      // Reload contracts if on the last page and it becomes empty
      const remainingContracts = (contracts || []).filter(c => c.id !== contractId);
      if (remainingContracts.length === 0 && currentPage > 1) {
        setCurrentPage(currentPage - 1);
      } else {
        loadContracts(); // Reload to get correct total pages and potentially new items if pagination changes
      }
    } catch (error: unknown) {
      console.error('Error deleting contract:', error);
      const apiError = error as APIError;
      const errorMessage = typeof apiError.detail === 'string' ? apiError.detail : 
                          Array.isArray(apiError.detail) ? (apiError.detail as ValidationError[]).map(d => d.msg).join(', ') :
                          'Failed to delete contract';
      toast.error(errorMessage);
    }
  };

  const handleViewDetails = (item: ContractHistoryItem) => {
    if (item.details) {
      setSelectedContractDetails(item.details);
    } else {
      console.warn("No details available for this contract in history item:", item);
      toast.error("Details not available for this contract.");
    }
  };

  const handleCloseModal = () => {
    setSelectedContractDetails(null);
  };
  // Client-side filtering based on searchTerm
  const filteredContracts = (contracts || []).filter(contract => {
    const term = searchTerm.toLowerCase();
    return (
      contract.id.toLowerCase().includes(term) ||
      (contract.contract_name && contract.contract_name.toLowerCase().includes(term)) ||
      (contract.contract_address && contract.contract_address.toLowerCase().includes(term)) ||
      (contract.blockchain && contract.blockchain.toLowerCase().includes(term))
      // Add more fields to search if needed, e.g., from contract.details
    );
  });
    // Download functionality
  const handleDownloadContract = (contract: ContractHistoryItem, type: 'original' | 'rewritten') => {
    let codeToDownload = '';
    let filename = '';
    
    if (type === 'original' && contract.details?.original_code) {
      codeToDownload = contract.details.original_code;
      filename = `${contract.contract_name || contract.id}_original.sol`;
    } else if (type === 'rewritten' && contract.details?.rewritten_code) {
      codeToDownload = contract.details.rewritten_code;
      filename = `${contract.contract_name || contract.id}_optimized.sol`;
    }
    
    if (codeToDownload) {
      // Create blob and download
      const blob = new Blob([codeToDownload], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success(`Downloaded ${filename}`);
    } else {
      toast.error(`${type === 'original' ? 'Original' : 'Optimized'} code not available for download.`);
    }
  };


  if (isLoading && contracts.length === 0) { // Show spinner only on initial load
    return (
      <div className="flex justify-center items-center h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error && contracts.length === 0) { // Show error only if no data could be loaded
    return (
      <div className="flex flex-col justify-center items-center h-screen text-red-500">
        <p className="text-2xl mb-4">Error loading contract history</p>
        <p>{error}</p>
        <Button onClick={loadContracts} className="mt-4">Try Again</Button>
      </div>
    );
  }

  const ContractDetailsModal: React.FC = () => {
    if (!selectedContractDetails) return null;

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={handleCloseModal}
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
              <h2 className="text-2xl font-semibold text-gray-800">
                Contract Details
              </h2>
              <Button variant="ghost" size="sm" onClick={handleCloseModal}>
                <X className="h-6 w-6" /> {/* Assuming X icon for close */}
              </Button>
            </div>

            {selectedContractDetails.analysis_report && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-gray-700 mb-3">Analysis Report</h3>
                <AnalysisDisplay report={selectedContractDetails.analysis_report} />
              </div>
            )}            {selectedContractDetails.rewrite_report && (
              <div>
                <h3 className="text-xl font-semibold text-gray-700 mb-3">Rewrite Report</h3>
                <RewriteDisplay 
                  report={selectedContractDetails.rewrite_report}
                  originalCode={selectedContractDetails.original_code || "Original code not available"}
                  rewrittenCode={selectedContractDetails.rewritten_code || selectedContractDetails.rewrite_report.rewritten_code || "Rewritten code not available"}
                  isLoading={false}
                  error={null}
                />
              </div>
            )}
            
            {!selectedContractDetails.analysis_report && !selectedContractDetails.rewrite_report && (
                <p className="text-gray-600">No analysis or rewrite details available for this contract.</p>
            )}

          </div>
        </motion.div>
      </motion.div>
    );
  };

  return (
    <div className="container mx-auto p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-800">Contract History</h1>
        <p className="text-gray-600 mt-1">
          Browse, view, and manage your past smart contract analyses and rewrites.
        </p>
      </motion.div>

      <div className="mb-6 flex flex-col md:flex-row gap-4 items-center">
        <div className="relative flex-grow w-full md:w-auto">
          <Input
            type="text"
            placeholder="Search by ID, Name, Address, Chain..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 w-full"
          />
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        </div>
        {/* Filter and Sort controls can be added here if needed */}
        {/* Example:
        <Select value={filterCriteria} onChange={(e) => setFilterCriteria(e.target.value as any)}>
          <option value=\"all\">All</option>
          <option value=\"contract_type\">Type</option>
          <option value=\"vulnerabilities\">Vulnerabilities</option>
        </Select>
        <Select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}>
          <option value=\"desc\">Newest First</option>
          <option value=\"asc\">Oldest First</option>
        </Select>
        */}
      </div>

      {isLoading && contracts.length > 0 && ( // Show loading indicator for subsequent loads
        <div className="flex justify-center my-4">
          <Spinner />
        </div>
      )}

      {filteredContracts.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Calendar className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">No Contracts Found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm ? "Try adjusting your search or filter terms." : "You haven't analyzed or rewritten any contracts yet."}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredContracts.map(contract => (
          <ContractCard 
            key={contract.id} 
            contract={contract} 
            onViewDetails={handleViewDetails} 
            onDeleteContract={handleDeleteContract} 
            onDownloadContract={handleDownloadContract} 
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="mt-8 flex justify-center items-center space-x-2">
          <Button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            variant="outline"
          >
            Previous
          </Button>
          <span className="text-gray-700">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            variant="outline"
          >
            Next
          </Button>
        </div>
      )}

      {selectedContractDetails && <ContractDetailsModal />}
    </div>
  );
};

export default ContractHistoryPage;

// Helper component for Contract Card (can be moved to a separate file)
const ContractCard: React.FC<{ 
  contract: ContractHistoryItem;
  onViewDetails: (contract: ContractHistoryItem) => void;
  onDeleteContract: (contractId: string) => void;
  onDownloadContract: (contract: ContractHistoryItem, type: 'original' | 'rewritten') => void;
}> = ({ contract, onViewDetails, onDeleteContract, onDownloadContract }) => {
    const getOptimizationSummary = (item: ContractHistoryItem) => {
    let gasSavings = 0;
    let securityIssues = 0;
    let optimizations = 0;

    if (item.type === 'analysis' && item.details?.analysis_report) {
      // For analysis items, count vulnerabilities and gas analysis
      const analysisReport = item.details.analysis_report;
      securityIssues = analysisReport.vulnerabilities?.length || 0;
      optimizations = analysisReport.gas_analysis_per_function?.length || 0;
      
      // Check if there's gas savings data in analysis
      if (analysisReport.total_gas_savings_percentage) {
        gasSavings = analysisReport.total_gas_savings_percentage;
      }
    } else if (item.type === 'rewrite' && item.details) {
      // For rewrite items, extract from rewrite_summary or details
      if (item.details.gas_savings_percentage) {
        gasSavings = item.details.gas_savings_percentage;
      }
      
      // Count changes as optimizations
      optimizations = item.details.changes_count || 0;
      
      // If there's a rewrite_summary with analysis data
      if (item.details.rewrite_summary && typeof item.details.rewrite_summary === 'object') {
        const rewriteData = item.details.rewrite_summary as any;
        if (rewriteData.analysis_of_rewritten_code?.vulnerabilities) {
          securityIssues = rewriteData.analysis_of_rewritten_code.vulnerabilities.length;
        }
        if (rewriteData.analysis_of_rewritten_code?.total_gas_savings_percentage) {
          gasSavings = rewriteData.analysis_of_rewritten_code.total_gas_savings_percentage;
        }
      }
    }

    return {
      gasSavings: Math.max(0, gasSavings || 0),
      securityIssues: Math.max(0, securityIssues || 0),
      optimizations: Math.max(0, optimizations || 0)
    };
  };
  const summary = getOptimizationSummary(contract);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-md p-5 hover:shadow-xl transition-shadow duration-300 flex flex-col justify-between"
    >
      <div>
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0"> {/* Added min-w-0 for truncation */}
            <h3 className="text-lg font-semibold text-gray-800 truncate" title={contract.contract_name || `Contract ID: ${contract.id}`}>
              {contract.contract_name || `Contract #${contract.id.slice(0,8)}...`}
            </h3>
            {contract.contract_address && (
              <p className="text-xs text-gray-500 truncate" title={contract.contract_address}>
                Address: {contract.contract_address}
              </p>
            )}
            {contract.blockchain && (
              <p className="text-xs text-gray-500">
                Chain: {contract.blockchain}
              </p>
            )}
            <p className="text-sm text-gray-500 mt-1">
              {formatDate(contract.timestamp)}
            </p>
          </div>
          <div className="flex flex-col space-y-1 ml-2"> {/* Changed to flex-col and added ml-2 */}            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewDetails(contract)}
              title="View Details"
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDeleteContract(contract.id)}
              className="text-red-500 hover:text-red-700"
              title="Delete Contract"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-x-2 gap-y-1 mb-4 text-xs"> {/* Reduced gap and text size */}
          <div className="text-center p-1 bg-green-50 rounded">
            <p className="text-gray-600">Gas Saved</p>
            <p className="font-bold text-green-600">
              {summary.gasSavings.toFixed(1)}%
            </p>
          </div>
          <div className="text-center p-1 bg-orange-50 rounded">
            <p className="text-gray-600">Issues</p>
            <p className="font-bold text-orange-600">
              {summary.securityIssues}
            </p>
          </div>
          <div className="text-center p-1 bg-blue-50 rounded">
            <p className="text-gray-600">Optimized</p>
            <p className="font-bold text-blue-600">
              {summary.optimizations}
            </p>
          </div>
        </div>
      </div>

      <div className="flex space-x-2 mt-auto"> {/* Added mt-auto to push to bottom */}        <Button
          variant="outline"
          size="sm"
          onClick={() => onDownloadContract(contract, 'original')}
          className="flex-1"
          disabled={!contract.details?.original_code}
        >
          <Download className="h-4 w-4 mr-1" />
          Original
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onDownloadContract(contract, 'rewritten')}
          className="flex-1"
          disabled={!contract.details?.rewritten_code && !contract.details?.rewrite_report?.rewritten_code}
        >
          <Download className="h-4 w-4 mr-1" />
          Optimized
        </Button>
      </div>
    </motion.div>
  );
};
