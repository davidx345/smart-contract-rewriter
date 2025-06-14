import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Shield, Zap, TrendingUp, CheckCircle, XCircle } from 'lucide-react';
import Card from '../ui/Card';
import type { AnalysisReport, VulnerabilityInfo, GasFunctionAnalysis } from '../../types'; // MODIFIED: Added GasFunctionAnalysis

interface AnalysisDisplayProps {
  report: AnalysisReport;
  className?: string;
}

const VulnerabilityItem: React.FC<{ vulnerability: VulnerabilityInfo }> = ({ vulnerability }) => {
  const severityColors = {
    Low: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    Medium: 'text-orange-600 bg-orange-50 border-orange-200',
    High: 'text-red-600 bg-red-50 border-red-200',
    Critical: 'text-red-800 bg-red-100 border-red-300'
  };

  const severityIcons = {
    Low: AlertTriangle,
    Medium: AlertTriangle,
    High: XCircle,
    Critical: XCircle
  };

  const severity = vulnerability.severity as keyof typeof severityColors;
  const colorClass = severityColors[severity] || severityColors.Medium;
  const Icon = severityIcons[severity] || AlertTriangle;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 rounded-lg border ${colorClass}`}
    >
      <div className="flex items-start space-x-3">
        <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <h4 className="font-medium">{vulnerability.type}</h4>
            <span className="text-xs font-semibold px-2 py-1 rounded-full bg-white/50">
              {vulnerability.severity}
            </span>
          </div>
          <p className="text-sm mb-2">{vulnerability.description}</p>
          {vulnerability.line_number && (
            <p className="text-xs opacity-75 mb-2">Line: {vulnerability.line_number}</p>
          )}
          <p className="text-sm font-medium">Recommendation:</p>
          <p className="text-xs">{vulnerability.recommendation}</p>
        </div>
      </div>
    </motion.div>
  );
};

const GasFunctionItem: React.FC<{ gasAnalysis: GasFunctionAnalysis }> = ({ gasAnalysis }) => { // MODIFIED: Used GasFunctionAnalysis type
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 rounded-lg border border-green-200 bg-green-50"
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-medium">{gasAnalysis.function_name}</h4>
        {gasAnalysis.savings_percentage && (
          <span className="text-xs font-semibold px-2 py-1 rounded-full bg-green-100 text-green-700">
            {gasAnalysis.savings_percentage.toFixed(1)}% savings
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4 text-sm">
        {gasAnalysis.original_gas && (
          <p>Original Gas: <span className="font-medium">{gasAnalysis.original_gas.toLocaleString()}</span></p>
        )}
        {gasAnalysis.optimized_gas && (
          <p>Optimized Gas: <span className="font-medium">{gasAnalysis.optimized_gas.toLocaleString()}</span></p>
        )}
      </div>
      {gasAnalysis.savings_absolute && (
        <p className="text-xs font-medium text-green-600 mt-2">
          Gas Savings: {gasAnalysis.savings_absolute.toLocaleString()}
        </p>
      )}
    </motion.div>
  );
};

const AnalysisDisplay: React.FC<AnalysisDisplayProps> = ({ report, className }) => {
  const getScoreColor = (score?: number) => {
    if (!score) return 'text-gray-500';
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  // The getRiskColor function has been completely removed.

  const vulnerabilities = report.vulnerabilities || [];
  const gasAnalysisPerFunction = report.gas_analysis_per_function || [];
  const generalSuggestions = report.general_suggestions || [];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center space-x-3">
            <Shield className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">Security Score</p>
              <p className={`text-2xl font-bold ${getScoreColor(report.overall_security_score)}`}>
                {report.overall_security_score ? `${report.overall_security_score}/10` : 'N/A'}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <TrendingUp className="h-8 w-8 text-purple-500" />
            <div>
              <p className="text-sm text-gray-600">Code Quality</p>
              <p className={`text-2xl font-bold ${getScoreColor(report.overall_code_quality_score)}`}>
                {report.overall_code_quality_score ? `${report.overall_code_quality_score}/10` : 'N/A'}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <div>
              <p className="text-sm text-gray-600">Vulnerabilities</p>
              <p className="text-2xl font-bold text-gray-900">
                {vulnerabilities.length} {/* MODIFIED: Use derived constant */}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <Zap className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">Estimated Gas</p>
              <p className="text-2xl font-bold text-gray-900">
                {report.estimated_total_gas_original ? report.estimated_total_gas_original.toLocaleString() : 'N/A'}
              </p>
            </div>
          </div>
        </Card>
      </div> {/* MODIFIED: Extra closing tags were removed from here in previous attempt, ensured correctness */}

      {/* Vulnerabilities Section */}
      {vulnerabilities.length > 0 && ( /* MODIFIED: Use derived constant */
        <Card title="Security Vulnerabilities">
          <div className="space-y-4">
            {vulnerabilities.map((vulnerability, index) => ( /* MODIFIED: Use derived constant */
              <VulnerabilityItem key={index} vulnerability={vulnerability} />
            ))}
          </div>
        </Card>
      )}

      {/* Gas Analysis Section */}
      {gasAnalysisPerFunction.length > 0 && ( /* MODIFIED: Use derived constant */
        <Card title="Gas Analysis Per Function">
          <div className="space-y-4">
            {gasAnalysisPerFunction.map((gasAnalysis, index) => ( /* MODIFIED: Use derived constant */
              <GasFunctionItem key={index} gasAnalysis={gasAnalysis} />
            ))}
          </div>
        </Card>
      )}

      {/* General Suggestions */}
      {generalSuggestions.length > 0 && ( /* MODIFIED: Use derived constant */
        <Card title="General Suggestions">
          <div className="space-y-2">
            {generalSuggestions.map((suggestion, index) => ( /* MODIFIED: Use derived constant */
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start space-x-2"
              >
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-gray-700">{suggestion}</p>
              </motion.div>
            ))}
          </div>
        </Card>
      )}

      {/* Gas Savings Summary */}
      {(report.total_gas_savings_absolute || report.total_gas_savings_percentage) && (
        <Card title="Gas Optimization Summary">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {report.estimated_total_gas_original && (
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Original Gas</p>
                <p className="text-xl font-bold text-gray-900">
                  {report.estimated_total_gas_original.toLocaleString()}
                </p>
              </div>
            )}
            {report.estimated_total_gas_optimized && (
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Optimized Gas</p>
                <p className="text-xl font-bold text-green-600">
                  {report.estimated_total_gas_optimized.toLocaleString()}
                </p>
              </div>
            )}
            {report.total_gas_savings_percentage && (
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Gas Savings</p>
                <p className="text-xl font-bold text-green-600">
                  {report.total_gas_savings_percentage.toFixed(1)}%
                </p>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default AnalysisDisplay;
