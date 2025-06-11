import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import ContractFormComponent from '../components/contract/ContractForm';
import AnalysisDisplay from '../components/contract/AnalysisDisplay';
import RewriteDisplay from '../components/contract/RewriteDisplay';
import Spinner from '../components/ui/Spinner';
import type { ContractForm, AnalysisReport, RewriteReport, ContractOutput, APIError, ValidationError } from '../types';
import { apiService } from '../services/api';

const HomePage: React.FC = () => {
  const [analysisReport, setAnalysisReport] = useState<AnalysisReport | null>(null);
  const [rewriteReport, setRewriteReport] = useState<RewriteReport | null>(null);
  const [rewrittenCode, setRewrittenCode] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRewriting, setIsRewriting] = useState(false);
  const [activeView, setActiveView] = useState<'form' | 'analysis' | 'rewrite'>('form');  const handleAnalyze = async (formData: ContractForm) => {
    setIsAnalyzing(true);
    try {
      // Extract contract name from code if not provided
      const extractContractName = (code: string): string => {
        const match = code.match(/contract\s+(\w+)/);
        return match ? match[1] : "UntitledContract";
      };

      const contractInput = {
        source_code: formData.contract_code,
        contract_name: formData.contract_name?.trim() || extractContractName(formData.contract_code),
        compiler_version: formData.target_solidity_version || "0.8.19"
      };

      const report = await apiService.analyzeContract(contractInput);
      setAnalysisReport(report);
      setActiveView('analysis');      toast.success('Contract analysis completed!');
    } catch (error: unknown) {
      const apiError = error as APIError;
      console.error('Analysis failed:', error);
        // Better error handling - extract meaningful message
      let errorMessage = 'Failed to analyze contract';
      if (apiError.detail) {
        if (Array.isArray(apiError.detail)) {
          // Handle Pydantic validation errors
          errorMessage = apiError.detail.map((err: ValidationError) => err.msg || String(err)).join(', ');
        } else {
          errorMessage = apiError.detail;
        }
      }
      
      toast.error(errorMessage);
    } finally {
      setIsAnalyzing(false);
    }
  };  const handleRewrite = async (formData: ContractForm) => {
    setIsRewriting(true);
    try {
      // Extract contract name from code if not provided
      const extractContractName = (code: string): string => {
        const match = code.match(/contract\s+(\w+)/);
        return match ? match[1] : "UntitledContract";
      };

      // Map frontend focus areas to backend optimization goals
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
      };      const result: ContractOutput = await apiService.rewriteContract(optimizationRequest);
      setRewriteReport(result.rewrite_report);
      setRewrittenCode(result.rewritten_code);
      setAnalysisReport(result.analysis_report);
      setActiveView('rewrite');      toast.success('Contract rewrite completed!');
    } catch (error: unknown) {
      const apiError = error as APIError;
      console.error('Rewrite failed:', error);
        // Better error handling - extract meaningful message
      let errorMessage = 'Failed to rewrite contract';
      if (apiError.detail) {
        if (Array.isArray(apiError.detail)) {
          // Handle Pydantic validation errors
          errorMessage = apiError.detail.map((err: ValidationError) => err.msg || String(err)).join(', ');
        } else {
          errorMessage = apiError.detail;
        }
      }
      
      toast.error(errorMessage);
    } finally {
      setIsRewriting(false);
    }
  };

  const resetView = () => {
    setActiveView('form');
    setAnalysisReport(null);
    setRewriteReport(null);
    setRewrittenCode('');
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
          transition={{ duration: 0.4 }}
        >
          {activeView === 'form' && (
            <div className="max-w-4xl mx-auto">
              <ContractFormComponent
                onAnalyze={handleAnalyze}
                onRewrite={handleRewrite}
                isAnalyzing={isAnalyzing}
                isRewriting={isRewriting}
              />
            </div>
          )}

          {activeView === 'analysis' && analysisReport && (
            <div className="max-w-7xl mx-auto">
              <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  Contract Analysis Report
                </h2>
                <p className="text-gray-600">
                  Comprehensive analysis of your smart contract
                </p>
              </div>
              <AnalysisDisplay report={analysisReport} />
            </div>
          )}

          {activeView === 'rewrite' && rewriteReport && (
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
                report={rewriteReport}
                rewrittenCode={rewrittenCode}
              />
            </div>
          )}
        </motion.div>

        {/* Loading States */}
        {(isAnalyzing || isRewriting) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          >
            <div className="bg-white rounded-lg p-8 max-w-md mx-4">
              <div className="text-center">
                <Spinner size="lg" className="mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {isAnalyzing ? 'Analyzing Contract...' : 'Rewriting Contract...'}
                </h3>
                <p className="text-gray-600">
                  {isAnalyzing 
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
