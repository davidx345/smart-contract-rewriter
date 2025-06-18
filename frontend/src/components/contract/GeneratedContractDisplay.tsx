import React from 'react';
import { motion } from 'framer-motion';
import { Copy, Download, Sparkles, CheckCircle, AlertTriangle, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';
import Button from '../ui/Button';
import Card from '../ui/Card';
import type { ContractOutput } from '../../types';

interface GeneratedContractDisplayProps {
  contractOutput: ContractOutput;
  isLoading?: boolean;
}

const GeneratedContractDisplay: React.FC<GeneratedContractDisplayProps> = ({
  contractOutput,
  isLoading = false
}) => {
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Contract code copied to clipboard!');
    } catch (err) {
      toast.error('Failed to copy code');
    }
  };

  const downloadContract = () => {
    const contractName = contractOutput.original_code.match(/contract\s+(\w+)/)?.[1] || 'GeneratedContract';
    const element = document.createElement('a');
    const file = new Blob([contractOutput.original_code], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `${contractName}.sol`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    toast.success('Contract downloaded successfully!');
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600">Generating your smart contract...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* Header */}
      <Card className="p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 text-green-600 rounded-lg">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Contract Generated Successfully!
              </h2>
              <p className="text-gray-600">
                {contractOutput.generation_notes || 'Your smart contract has been generated using AI'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {contractOutput.compilation_success_original && (
              <div className="flex items-center space-x-1 text-green-600">
                <CheckCircle className="w-5 h-5" />
                <span className="text-sm font-medium">Compiles Successfully</span>
              </div>
            )}
            {contractOutput.confidence_score && (
              <div className="text-sm text-gray-500">
                Confidence: {Math.round(contractOutput.confidence_score * 100)}%
              </div>
            )}
          </div>
        </div>
      </Card>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Generated Contract Code */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <FileText className="w-5 h-5" />
                <span>Generated Contract</span>
              </h3>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(contractOutput.original_code)}
                  className="flex items-center space-x-1"
                >
                  <Copy className="w-4 h-4" />
                  <span>Copy</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={downloadContract}
                  className="flex items-center space-x-1"
                >
                  <Download className="w-4 h-4" />
                  <span>Download</span>
                </Button>
              </div>
            </div>
            
            <div className="relative">
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                <code>{contractOutput.original_code}</code>
              </pre>
            </div>
          </Card>
        </div>

        {/* Analysis and Info */}
        <div className="space-y-6">
          {/* Compilation Status */}
          <Card className="p-4">
            <h4 className="text-md font-semibold text-gray-900 mb-3">
              Compilation Status
            </h4>
            <div className="flex items-center space-x-2">
              {contractOutput.compilation_success_original ? (
                <>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="text-green-600 font-medium">Compiles Successfully</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  <span className="text-red-600 font-medium">Compilation Issues</span>
                </>
              )}
            </div>
          </Card>

          {/* Contract Info */}
          <Card className="p-4">
            <h4 className="text-md font-semibold text-gray-900 mb-3">
              Contract Information
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Processing Time:</span>
                <span className="font-medium">
                  {contractOutput.processing_time_seconds.toFixed(2)}s
                </span>
              </div>
              {contractOutput.confidence_score && (
                <div className="flex justify-between">
                  <span className="text-gray-600">AI Confidence:</span>
                  <span className="font-medium">
                    {Math.round(contractOutput.confidence_score * 100)}%
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Lines of Code:</span>
                <span className="font-medium">
                  {contractOutput.original_code.split('\n').length}
                </span>
              </div>
            </div>
          </Card>

          {/* Analysis Report */}
          {contractOutput.analysis_report && (
            <Card className="p-4">
              <h4 className="text-md font-semibold text-gray-900 mb-3">
                Security Analysis
              </h4>
              <div className="space-y-3">
                {contractOutput.analysis_report.vulnerabilities.length > 0 ? (
                  <div>
                    <p className="text-sm text-red-600 font-medium mb-2">
                      {contractOutput.analysis_report.vulnerabilities.length} Potential Issues Found
                    </p>
                    <div className="space-y-2">
                      {contractOutput.analysis_report.vulnerabilities.slice(0, 3).map((vuln, index) => (
                        <div key={index} className="p-2 bg-red-50 border border-red-200 rounded text-xs">
                          <div className="font-medium text-red-800">{vuln.type}</div>
                          <div className="text-red-600">{vuln.description}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">No Security Issues Detected</span>
                  </div>
                )}

                {contractOutput.analysis_report.general_suggestions.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Suggestions:</p>
                    <ul className="space-y-1">
                      {contractOutput.analysis_report.general_suggestions.slice(0, 3).map((suggestion, index) => (
                        <li key={index} className="text-xs text-gray-600">
                          • {suggestion}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Next Steps */}
          <Card className="p-4">
            <h4 className="text-md font-semibold text-gray-900 mb-3">
              Next Steps
            </h4>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-start space-x-2">
                <span className="text-primary-600 font-bold">1.</span>
                <span>Review the generated contract code carefully</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-primary-600 font-bold">2.</span>
                <span>Test the contract in a development environment</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-primary-600 font-bold">3.</span>
                <span>Consider professional security audit before deployment</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-primary-600 font-bold">4.</span>
                <span>Deploy to testnet first, then mainnet</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </motion.div>
  );
};

export default GeneratedContractDisplay;
