import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import ContractFormComponent from '../components/contract/ContractForm';
import ContractGenerator from '../components/contract/ContractGenerator';
import GeneratedContractDisplay from '../components/contract/GeneratedContractDisplay';
import AnalysisDisplay from '../components/contract/AnalysisDisplay';
import RewriteDisplay from '../components/contract/RewriteDisplay';
import { AdvancedAnalysisDisplay } from '../components/contract/AdvancedAnalysisDisplay';
import { AIContractGenerator } from '../components/contract/AIContractGenerator';
import Spinner from '../components/ui/Spinner';
import { apiService } from '../services/api';
import type { ContractForm, ContractGenerationForm, ContractOutput, APIError, ValidationError } from '../types';

// Define props for HomePage
interface HomePageProps {
  contractOutput: ContractOutput | null;
  setContractOutput: React.Dispatch<React.SetStateAction<ContractOutput | null>>;
  activeView: 'form' | 'analysis' | 'rewrite' | 'generate' | 'generated' | 'ai-analysis' | 'ai-generate';
  setActiveView: React.Dispatch<React.SetStateAction<'form' | 'analysis' | 'rewrite' | 'generate' | 'generated' | 'ai-analysis' | 'ai-generate'>>;
}

const HomePage: React.FC<HomePageProps> = ({ 
  contractOutput, 
  setContractOutput, 
  activeView, 
  setActiveView 
}) => {
  const [loadingAction, setLoadingAction] = useState<'analyze' | 'rewrite' | 'generate' | null>(null);
  const [error, setError] = useState<string | null>(null); // UI error state

  // Effect to synchronize local state if global state changes externally (e.g. browser back button)
  useEffect(() => {
    // This effect can be expanded if more granular control is needed
    // For now, it ensures that if contractOutput is null globally, the view resets to form.
    if (contractOutput === null && activeView !== 'form') {
      // setActiveView('form'); // This might be too aggressive, consider user experience
    }
  }, [contractOutput, activeView, setActiveView]);

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
        contract_code: formData.contract_code,
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
        contract_code: formData.contract_code,
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

  const handleGenerate = async (formData: ContractGenerationForm) => {
    setLoadingAction('generate');
    setError(null);
    setContractOutput(null);
    
    try {
      const generationRequest = {
        description: formData.description,
        contract_name: formData.contract_name,
        features: formData.features,
        compiler_version: formData.target_solidity_version
      };
      
      const result: ContractOutput = await apiService.generateContract(generationRequest);
      setContractOutput(result);
      
      // Fix: Check rewritten_code instead of original_code for generated contracts
      if (result.rewritten_code || result.original_code) {
        setActiveView('generated');
        toast.success(result.message || 'Smart contract generated successfully!');
      } else {
        setError(result.message || 'Contract generation did not produce code.');
        toast.error(result.message || 'Contract generation did not produce code.');
      }
    } catch (err: unknown) {
      const apiError = err as APIError;
      console.error('Contract generation failed:', err);
      setContractOutput(null);
      let errorMessage = 'Failed to generate contract';
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
      setLoadingAction(null);
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
          >            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              SoliVolt
            </h1><p className="text-xl md:text-2xl mb-8 text-blue-100">
              AI-powered analysis, optimization, and generation for your Solidity contracts
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
              </div>              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <span>Best Practices</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-indigo-400 rounded-full"></div>
                <span>AI Generation</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>      {/* Main Content */}
      <div className="container mx-auto px-6 py-12">
        {/* Main Navigation Tabs */}
        {(activeView === 'form' || activeView === 'analysis' || activeView === 'rewrite') && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <div className="flex justify-center">
              <div className="flex flex-wrap justify-center gap-1 p-1 bg-gray-100 rounded-lg">
                <button
                  onClick={() => setActiveView('form')}
                  className="px-4 py-2 text-sm font-medium rounded-md bg-primary-600 text-white shadow-sm"
                >
                  Smart Analysis
                </button>
                {/* <button
                  onClick={() => setActiveView('ai-analysis')}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                >
                  🤖 AI Analysis
                </button> */}
                <button
                  onClick={() => setActiveView('generate')}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                >
                  Generate Contract
                </button>
                {/* <button
                  onClick={() => setActiveView('ai-generate')}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                >
                  🚀 AI Generator
                </button> */}
              </div>
            </div>
          </motion.div>
        )}
        
        {activeView === 'generate' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <div className="flex justify-center">
              <div className="flex flex-wrap justify-center gap-1 p-1 bg-gray-100 rounded-lg">
                <button
                  onClick={() => setActiveView('form')}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                >
                  Basic Analysis
                </button>
                {/* <button
                  onClick={() => setActiveView('ai-analysis')}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                >
                  🤖 AI Analysis
                </button> */}
                <button
                  onClick={() => setActiveView('generate')}
                  className="px-4 py-2 text-sm font-medium rounded-md bg-primary-600 text-white shadow-sm"
                >
                  Generate Contract
                </button>
                {/* <button
                  onClick={() => setActiveView('ai-generate')}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                >
                  🚀 AI Generator
                </button> */}
              </div>
            </div>
          </motion.div>
        )}

        {(activeView === 'ai-analysis' || activeView === 'ai-generate') && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <div className="flex justify-center">
              <div className="flex flex-wrap justify-center gap-1 p-1 bg-gray-100 rounded-lg">
                <button
                  onClick={() => setActiveView('form')}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                >
                  Basic Analysis
                </button>
                {/* <button
                  onClick={() => setActiveView('ai-analysis')}
                  className={`px-4 py-2 text-sm font-medium rounded-md ${
                    activeView === 'ai-analysis' 
                      ? 'bg-blue-600 text-white shadow-sm' 
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  🤖 AI Analysis
                </button> */}
                <button
                  onClick={() => setActiveView('generate')}
                  className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                >
                  Generate Contract
                </button>
                {/* <button
                  onClick={() => setActiveView('ai-generate')}
                  className={`px-4 py-2 text-sm font-medium rounded-md ${
                    activeView === 'ai-generate' 
                      ? 'bg-purple-600 text-white shadow-sm' 
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  🚀 AI Generator
                </button> */}
              </div>
            </div>
          </motion.div>
        )}

        {/* Navigation Breadcrumbs */}
        {(activeView !== 'form' && activeView !== 'generate' && activeView !== 'ai-analysis' && activeView !== 'ai-generate') && (
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
            </div>          )}

          {activeView === 'generate' && (
            <div className="max-w-4xl mx-auto">
              <ContractGenerator 
                onGenerate={handleGenerate}
                isGenerating={loadingAction === 'generate'}
              />
            </div>
          )}

          {activeView === 'generated' && (contractOutput?.rewritten_code || contractOutput?.original_code) && (
            <div className="max-w-7xl mx-auto">
              <GeneratedContractDisplay
                contractOutput={contractOutput}
                isLoading={loadingAction === 'generate'}
              />
            </div>
          )}

          {activeView === 'ai-analysis' && (
            <div className="max-w-7xl mx-auto">
              <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  🤖 Advanced AI Analysis
                </h2>
                <p className="text-gray-600">
                  Comprehensive ML-powered security analysis and optimization
                </p>
              </div>
              <AdvancedAnalysisDisplay 
                contractCode={contractOutput?.original_code || ''} 
                onAnalysisComplete={(analysis) => {
                  // Handle analysis completion if needed
                  console.log('AI Analysis completed:', analysis);
                }}
              />
            </div>
          )}

          {activeView === 'ai-generate' && (
            <div className="max-w-7xl mx-auto">
              <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  🚀 AI Contract Generator
                </h2>
                <p className="text-gray-600">
                  Generate production-ready smart contracts using advanced AI
                </p>
              </div>
              <AIContractGenerator />
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
                  {loadingAction === 'analyze' ? 'Analyzing Contract...' : loadingAction === 'rewrite' ? 'Rewriting Contract...' : 'Generating Contract...'}
                </h3>
                <p className="text-gray-600">
                  {loadingAction === 'analyze' 
                    ? 'AI is analyzing your contract for security issues and optimization opportunities.'
                    : loadingAction === 'rewrite'
                    ? 'AI is rewriting your contract with optimizations and improvements.'
                    : 'AI is generating a new smart contract based on your specifications.'
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
      
      {/* Features Section (shown only on form and generate views) */}
      {(activeView === 'form' || activeView === 'generate') && (
        <div className="bg-white py-16"> {/* Ensure this div has a className and proper structure */}
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900">
                Powerful Features
              </h2>
              <p className="text-gray-600 mt-2">
                Leverage AI to enhance your smart contracts in multiple ways.
              </p>
            </div>            <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-8">
              {[
                {
                  title: 'Gas Optimization',
                  description: 'Reduce transaction costs by optimizing gas usage',
                  color: 'bg-yellow-100 text-yellow-600'
                },
                {
                  title: 'Security Analysis',
                  description: 'Identify vulnerabilities and security issues in your code',
                  color: 'bg-green-100 text-green-600'
                },
                {
                  title: 'Code Quality',
                  description: 'Improve readability, maintainability, and best practices',
                  color: 'bg-blue-100 text-blue-600'
                },
                {
                  title: 'Best Practices',
                  description: 'Apply industry standards and proven patterns',
                  color: 'bg-purple-100 text-purple-600'
                },
                {
                  title: 'AI Generation',
                  description: 'Generate smart contracts from natural language descriptions',
                  color: 'bg-indigo-100 text-indigo-600'
                }
              ].map((feature, index) => (
                <motion.div
                  key={feature.title} // Ensure key is a string
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 * index }}
                  className="text-center p-6 bg-gray-50 rounded-lg shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className={`w-16 h-16 ${feature.color} rounded-full flex items-center justify-center text-3xl mx-auto mb-4`}>
                    {feature.title.charAt(0)}
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-700 text-sm">
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
