import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Copy, Download, CheckCircle, TrendingDown, Zap, Shield, Code, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';
import Card from '../ui/Card';
import Button from '../ui/Button';
import type { RewriteReport, GasFunctionAnalysis } from '../../types';
import { copyToClipboard, downloadFile, formatGasAmount, calculateGasSavings } from '../../lib/utils.js';

interface RewriteDisplayProps {
  report: RewriteReport;
  rewrittenCode: string;
  className?: string;
}

const FunctionGasAnalysis: React.FC<{ analysis: GasFunctionAnalysis }> = ({ analysis }) => {
  const savings = calculateGasSavings(analysis.original_gas, analysis.optimized_gas);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-50 rounded-lg p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-gray-900">{analysis.function_name}</h4>
        <span className="text-sm font-medium text-green-600">
          -{savings.percentage.toFixed(1)}% gas
        </span>
      </div>
      
      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-gray-600">Original</p>
          <p className="font-medium">{formatGasAmount(analysis.original_gas)}</p>
        </div>
        <div>
          <p className="text-gray-600">Optimized</p>
          <p className="font-medium text-green-600">{formatGasAmount(analysis.optimized_gas)}</p>
        </div>
        <div>
          <p className="text-gray-600">Savings</p>
          <p className="font-medium text-green-600">{formatGasAmount(savings.absolute)}</p>
        </div>
      </div>
      
      {analysis.optimization_techniques.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-600 mb-1">Techniques:</p>
          <div className="flex flex-wrap gap-1">
            {analysis.optimization_techniques.map((technique, index) => (
              <span 
                key={index}
                className="inline-flex px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700"
              >
                {technique}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
};

const RewriteDisplay: React.FC<RewriteDisplayProps> = ({ 
  report, 
  rewrittenCode, 
  className 
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'code' | 'functions'>('overview');
  
  const gasSavings = calculateGasSavings(
    report.original_gas_estimate, 
    report.optimized_gas_estimate
  );

  const handleCopyCode = async () => {
    try {
      await copyToClipboard(rewrittenCode);
      toast.success('Code copied to clipboard!');
    } catch {
      toast.error('Failed to copy code');
    }
  };

  const handleDownloadCode = () => {
    downloadFile(rewrittenCode, 'optimized_contract.sol', 'text/plain');
    toast.success('Contract downloaded!');
  };

  const getCompilationStatusColor = (success: boolean) => {
    return success ? 'text-green-600 bg-green-50 border-green-200' : 'text-red-600 bg-red-50 border-red-200';
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center space-x-3">
            <TrendingDown className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">Gas Savings</p>
              <p className="text-2xl font-bold text-green-600">
                {gasSavings.percentage.toFixed(1)}%
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <Zap className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">Optimized Gas</p>
              <p className="text-2xl font-bold text-blue-600">
                {formatGasAmount(report.optimized_gas_estimate)}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <Shield className="h-8 w-8 text-purple-500" />
            <div>
              <p className="text-sm text-gray-600">Security Fixes</p>
              <p className="text-2xl font-bold text-purple-600">
                {report.security_improvements.length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <Code className="h-8 w-8 text-orange-500" />
            <div>
              <p className="text-sm text-gray-600">Techniques</p>
              <p className="text-2xl font-bold text-orange-600">
                {report.optimization_techniques_applied.length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: FileText },
            { id: 'code', label: 'Optimized Code', icon: Code },
            { id: 'functions', label: 'Function Analysis', icon: Zap }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'overview' | 'code' | 'functions')}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Gas Comparison */}
            <Card title="Gas Usage Comparison">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Original Estimate</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatGasAmount(report.original_gas_estimate)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Optimized Estimate</p>
                  <p className="text-3xl font-bold text-green-600">
                    {formatGasAmount(report.optimized_gas_estimate)}
                  </p>
                </div>
              </div>
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-600">Total Savings</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatGasAmount(gasSavings.absolute)} ({gasSavings.percentage.toFixed(1)}%)
                </p>
              </div>
            </Card>

            {/* Compilation Status */}
            <Card title="Compilation Status">
              <div className={`p-4 rounded-lg border ${getCompilationStatusColor(report.compilation_status.success)}`}>
                <div className="flex items-center space-x-2 mb-2">
                  <CheckCircle className="h-5 w-5" />
                  <span className="font-medium">
                    {report.compilation_status.success ? 'Compilation Successful' : 'Compilation Failed'}
                  </span>
                </div>
                <p className="text-sm">Compiler Version: {report.compilation_status.compiler_version}</p>
                
                {report.compilation_status.warnings.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium mb-1">Warnings:</p>
                    <ul className="text-sm space-y-1">
                      {report.compilation_status.warnings.map((warning, index) => (
                        <li key={index} className="flex items-start">
                          <span className="mr-2">⚠️</span>
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {report.compilation_status.errors.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium mb-1">Errors:</p>
                    <ul className="text-sm space-y-1">
                      {report.compilation_status.errors.map((error, index) => (
                        <li key={index} className="flex items-start">
                          <span className="mr-2">❌</span>
                          {error}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>

            {/* Improvements */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Security Improvements */}
              {report.security_improvements.length > 0 && (
                <Card title="Security Improvements">
                  <ul className="space-y-2">
                    {report.security_improvements.map((improvement, index) => (
                      <li key={index} className="flex items-start space-x-2 text-sm">
                        <Shield className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{improvement}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Optimization Techniques */}
              {report.optimization_techniques_applied.length > 0 && (
                <Card title="Optimization Techniques Applied">
                  <ul className="space-y-2">
                    {report.optimization_techniques_applied.map((technique, index) => (
                      <li key={index} className="flex items-start space-x-2 text-sm">
                        <Zap className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                        <span>{technique}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>

            {/* Code Quality Improvements */}
            {report.code_quality_improvements.length > 0 && (
              <Card title="Code Quality Improvements">
                <ul className="space-y-2">
                  {report.code_quality_improvements.map((improvement, index) => (
                    <li key={index} className="flex items-start space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-purple-500 mt-0.5 flex-shrink-0" />
                      <span>{improvement}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'code' && (
          <Card title="Optimized Contract Code">
            <div className="space-y-4">
              <div className="flex justify-end space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyCode}
                >
                  <Copy className="h-4 w-4 mr-1" />
                  Copy
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadCode}
                >
                  <Download className="h-4 w-4 mr-1" />
                  Download
                </Button>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap">
                  {rewrittenCode}
                </pre>
              </div>
            </div>
          </Card>
        )}

        {activeTab === 'functions' && (
          <Card title="Function-Level Gas Analysis">
            {report.function_gas_analysis.length > 0 ? (
              <div className="space-y-4">
                {report.function_gas_analysis.map((analysis, index) => (
                  <FunctionGasAnalysis key={index} analysis={analysis} />
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No function-level analysis available
              </p>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};

export default RewriteDisplay;
