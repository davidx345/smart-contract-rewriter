import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import ContractFormComponent from '../components/contract/ContractForm';
import AnalysisDisplay from '../components/contract/AnalysisDisplay';
import RewriteDisplay from '../components/contract/RewriteDisplay';
import Spinner from '../components/ui/Spinner';
import { apiService } from '../services/api';
import type { ContractForm, ContractOutput, APIError, ValidationError } from '../types';

const HomePage: React.FC = () => {
  const [contractOutput, setContractOutput] = useState<ContractOutput | null>(null);
  const [loadingAction, setLoadingAction] = useState<'analyze' | 'rewrite' | null>(null); // New state
  const [error, setError] = useState<string | null>(null); // UI error state
  const [activeView, setActiveView] = useState<'form' | 'analysis' | 'rewrite'>('form');

  const handleAnalyze = async (formData: ContractForm) => {
    setLoadingAction('analyze'); // Set specific loading action
    setError(null); // Clear UI error
    setContractOutput(null); // Clear previous output
    try {
      const extractContractName = (code: string): string => {
        const match = code.match(/contract\\s+(\\w+)/);
        return match ? match[1] : "UntitledContract";
      };

      const contractInput = {
        source_code: formData.contract_code,
        contract_name: formData.contract_name?.trim() || extractContractName(formData.contract_code),
        compiler_version: formData.target_solidity_version || "0.8.19"
      };
      const result: ContractOutput = await apiService.analyzeContract(contractInput);
      setContractOutput(result);
      if (result.analysis_report) {
        setActiveView('analysis');
        toast.success(result.message || 'Contract analysis completed!');
      } else {
        setError(result.message || 'Analysis did not produce a report.');
        toast.error(result.message || 'Analysis did not produce a report.');
      }
    } catch (err: unknown) {
      const apiError = err as APIError;
      console.error('Analysis failed:', err);
      setContractOutput(null);
      let errorMessage = 'Failed to analyze contract';
      if (apiError.detail) {
        if (Array.isArray(apiError.detail)) {
          errorMessage = apiError.detail.map((validationErr: ValidationError) => validationErr.msg || String(validationErr)).join(', ');
        } else {
          errorMessage = apiError.detail;
        }
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoadingAction(null); // Clear loading action
    }
  };
  
  const handleRewrite = async (formData: ContractForm) => {
    if (!formData.contract_code) {
      setError("Please enter some contract code.");
      return;
    }
    setLoadingAction('rewrite'); // Set specific loading action
    setError(null); // Clear UI error
    // Preserve analysis report if it exists, clear rewrite specific parts
    setContractOutput(prev => prev ? { ...prev, rewrite_report: undefined, rewritten_code: undefined, message: 'Processing rewrite...' } : null);
    try {
      const extractContractName = (code: string): string => {
        const match = code.match(/contract\\s+(\\w+)/);
        return match ? match[1] : "UntitledContract";
      };

      const optimizationGoalsMap = {
        'GAS_OPTIMIZATION': 'gas_efficiency',
        'SECURITY': 'security_hardening',
        'READABILITY': 'readability',
        'BEST_PRACTICES': 'modularity'
      } as const;

      const optimization_goals = formData.focus_areas.map(area =>
        optimizationGoalsMap[area as keyof typeof optimizationGoalsMap] || 'gas_efficiency'
      );

      const optimizationRequest = {
        source_code: formData.contract_code,
        contract_name: formData.contract_name?.trim() || extractContractName(formData.contract_code),
        compiler_version: formData.target_solidity_version || "0.8.19",
        optimization_goals,
        preserve_functionality: formData.preserve_functionality
      };
      const result: ContractOutput = await apiService.rewriteContract(optimizationRequest);
      // Update contractOutput with the new rewrite result, keeping existing analysis if any
      setContractOutput(prev => ({
        ...(prev || { original_code: formData.contract_code, request_id: '', processing_time_seconds: 0, message: '' }), // Ensure base structure if prev is null
        ...result // Spread the new result, overwriting relevant fields
      }));
      if (result.rewritten_code && result.rewrite_report) {
        setActiveView('rewrite');
        toast.success(result.message || 'Contract rewrite completed!');
      } else {
        setError(result.message || 'Rewrite did not produce the expected output.');
        toast.error(result.message || 'Rewrite did not produce the expected output.');
      }
    } catch (err: unknown) {
      const apiError = err as APIError;
      console.error('Rewrite failed:', err);
      let errorMessage = 'Failed to rewrite contract';
      if (apiError.detail) {
        if (Array.isArray(apiError.detail)) {
          errorMessage = apiError.detail.map((validationErr: ValidationError) => validationErr.msg || String(validationErr)).join(', ');
        } else {
          errorMessage = apiError.detail;
        }
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      // When rewrite fails, we might want to clear only rewrite-specific parts or keep existing state
      setContractOutput(prev => prev ? 
        { ...prev, rewrite_report: undefined, rewritten_code: undefined, message: errorMessage } : 
        { request_id: "", original_code: formData.contract_code, processing_time_seconds:0, message: errorMessage });
      toast.error(errorMessage);
    } finally {
      setLoadingAction(null); // Clear loading action
    }
  };

  const resetView = () => {
    setActiveView('form');
    setContractOutput(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="gradient-bg text-white">
        <div className="container mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Smart Contract Rewriter
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100">
              AI-powered optimization for your Solidity contracts
            </p>
            <div className="flex flex-wrap justify-center gap-6 text-sm md:text-base">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>Gas Optimization</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span>Security Analysis</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                <span>Code Quality</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <span>Best Practices</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-12">
        {/* Navigation Breadcrumbs */}
        {activeView !== 'form' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <nav className="flex items-center space-x-2 text-sm">
              <button 
                onClick={resetView}
                className="text-primary-600 hover:text-primary-800 transition-colors"
              >
                Contract Input
              </button>
              <span className="text-gray-400">/</span>
              <span className="text-gray-600 capitalize">{activeView}</span>
            </nav>
          </motion.div>
        )}

        {/* Content Views */}
        <motion.div
          key={activeView}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {activeView === 'form' && (
            <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-md p-8">
              <h2 className="text-2xl font-bold mb-6 text-center">
                Analyze and Rewrite Your Contract
              </h2>
              <ContractFormComponent 
                onAnalyze={handleAnalyze}
                onRewrite={handleRewrite}
                // Pass specific loading states
                isAnalyzing={loadingAction === 'analyze'}
                isRewriting={loadingAction === 'rewrite'}
              />
            </div>
          )}

          {activeView === 'analysis' && contractOutput?.analysis_report && (
            <div className="max-w-7xl mx-auto">
              <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  Contract Analysis Report
                </h2>
                <p className="text-gray-600">
                  Comprehensive analysis of your smart contract
                </p>
              </div>
              <AnalysisDisplay report={contractOutput.analysis_report} />
            </div>
          )}

          {activeView === 'rewrite' && contractOutput?.rewrite_report && contractOutput?.rewritten_code && contractOutput?.original_code && (
            <div className="max-w-7xl mx-auto">
              <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  Contract Optimization Report
                </h2>
                <p className="text-gray-600">
                  Your optimized smart contract with improvements
                </p>
              </div>
              <RewriteDisplay
                report={contractOutput.rewrite_report}
                originalCode={contractOutput.original_code}
                rewrittenCode={contractOutput.rewritten_code}
                isLoading={loadingAction === 'rewrite'} // Pass specific loading state
                error={error}
              />
            </div>
          )}
        </motion.div>

        {/* Loading States - Now uses loadingAction */}
        {loadingAction && ( // Show spinner if any action is loading
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          >
            <div className="bg-white rounded-lg p-8 max-w-md mx-4">
              <div className="text-center">
                <Spinner size="lg" className="mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {/* Update text based on loadingAction */}
                  {loadingAction === 'analyze' ? 'Analyzing Contract...' : 'Rewriting Contract...'}
                </h3>
                <p className="text-gray-600">
                  {loadingAction === 'analyze' 
                    ? 'AI is analyzing your contract for security issues and optimization opportunities.'
                    : 'AI is rewriting your contract with optimizations and improvements.'
                  }
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  This may take a few moments.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Features Section (shown only on form view) */}
      {activeView === 'form' && (
        <div className="bg-gray-50 py-16">
          <div className="container mx-auto px-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Powered by Advanced AI
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Our AI analyzes your smart contracts and provides comprehensive optimization recommendations
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                {
                  title: 'Gas Optimization',
                  description: 'Reduce transaction costs with intelligent gas usage optimization',
                  icon: '⚡',
                  color: 'bg-yellow-100 text-yellow-600'
                },
                {
                  title: 'Security Analysis',
                  description: 'Identify vulnerabilities and security issues in your code',
                  icon: '🛡️',
                  color: 'bg-green-100 text-green-600'
                },
                {
                  title: 'Code Quality',
                  description: 'Improve readability, maintainability, and best practices',
                  icon: '📝',
                  color: 'bg-blue-100 text-blue-600'
                },
                {
                  title: 'Best Practices',
                  description: 'Apply industry standards and proven patterns',
                  icon: '✨',
                  color: 'bg-purple-100 text-purple-600'
                }
              ].map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 * index }}
                  className="text-center"
                >
                  <div className={`w-16 h-16 ${feature.color} rounded-full flex items-center justify-center text-2xl mx-auto mb-4`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
