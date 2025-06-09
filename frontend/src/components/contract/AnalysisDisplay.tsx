import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Shield, Zap, TrendingUp, CheckCircle, XCircle } from 'lucide-react';
import Card from '../ui/Card';
import type { AnalysisReport, SecurityIssue, OptimizationSuggestion } from '../../types';

interface AnalysisDisplayProps {
  report: AnalysisReport;
  className?: string;
}

const SecurityIssueItem: React.FC<{ issue: SecurityIssue }> = ({ issue }) => {
  const severityColors = {
    LOW: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    MEDIUM: 'text-orange-600 bg-orange-50 border-orange-200',
    HIGH: 'text-red-600 bg-red-50 border-red-200',
    CRITICAL: 'text-red-800 bg-red-100 border-red-300'
  };

  const severityIcons = {
    LOW: AlertTriangle,
    MEDIUM: AlertTriangle,
    HIGH: XCircle,
    CRITICAL: XCircle
  };

  const Icon = severityIcons[issue.severity];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 rounded-lg border ${severityColors[issue.severity]}`}
    >
      <div className="flex items-start space-x-3">
        <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <h4 className="font-medium">{issue.category}</h4>
            <span className="text-xs font-semibold px-2 py-1 rounded-full bg-white/50">
              {issue.severity}
            </span>
          </div>
          <p className="text-sm mb-2">{issue.description}</p>
          {issue.line_number && (
            <p className="text-xs opacity-75 mb-2">Line: {issue.line_number}</p>
          )}
          <p className="text-sm font-medium">Recommendation:</p>
          <p className="text-xs">{issue.recommendation}</p>
        </div>
      </div>
    </motion.div>
  );
};

const OptimizationItem: React.FC<{ suggestion: OptimizationSuggestion }> = ({ suggestion }) => {
  const typeColors = {
    GAS_OPTIMIZATION: 'text-green-600 bg-green-50 border-green-200',
    SECURITY_IMPROVEMENT: 'text-blue-600 bg-blue-50 border-blue-200',
    CODE_QUALITY: 'text-purple-600 bg-purple-50 border-purple-200',
    PERFORMANCE: 'text-indigo-600 bg-indigo-50 border-indigo-200'
  };

  const impactColors = {
    LOW: 'bg-gray-100 text-gray-600',
    MEDIUM: 'bg-yellow-100 text-yellow-700',
    HIGH: 'bg-green-100 text-green-700'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 rounded-lg border ${typeColors[suggestion.type]}`}
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-medium">{suggestion.type.replace('_', ' ')}</h4>
        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${impactColors[suggestion.impact]}`}>
          {suggestion.impact} Impact
        </span>
      </div>
      <p className="text-sm mb-2">{suggestion.description}</p>
      {suggestion.estimated_gas_savings && (
        <p className="text-xs font-medium text-green-600">
          Estimated Gas Savings: {suggestion.estimated_gas_savings.toLocaleString()}
        </p>
      )}
      {suggestion.code_location && (
        <p className="text-xs opacity-75 mt-1">Location: {suggestion.code_location}</p>
      )}
    </motion.div>
  );
};

const AnalysisDisplay: React.FC<AnalysisDisplayProps> = ({ report, className }) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW': return 'text-green-600 bg-green-50 border-green-200';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'HIGH': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'CRITICAL': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center space-x-3">
            <Zap className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">Gas Efficiency</p>
              <p className={`text-2xl font-bold ${getScoreColor(report.gas_efficiency_score)}`}>
                {report.gas_efficiency_score}%
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <Shield className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">Security Issues</p>
              <p className="text-2xl font-bold text-gray-900">
                {report.security_issues.length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <TrendingUp className="h-8 w-8 text-purple-500" />
            <div>
              <p className="text-sm text-gray-600">Code Quality</p>
              <p className={`text-2xl font-bold ${getScoreColor(report.code_quality_metrics.complexity_score)}`}>
                {report.code_quality_metrics.complexity_score}%
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-8 w-8 text-orange-500" />
            <div>
              <p className="text-sm text-gray-600">Overall Risk</p>
              <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(report.vulnerability_assessment.overall_risk)}`}>
                {report.vulnerability_assessment.overall_risk}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Code Quality Metrics */}
      <Card title="Code Quality Metrics">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Complexity</p>
            <p className={`text-xl font-bold ${getScoreColor(report.code_quality_metrics.complexity_score)}`}>
              {report.code_quality_metrics.complexity_score}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Readability</p>
            <p className={`text-xl font-bold ${getScoreColor(report.code_quality_metrics.readability_score)}`}>
              {report.code_quality_metrics.readability_score}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Maintainability</p>
            <p className={`text-xl font-bold ${getScoreColor(report.code_quality_metrics.maintainability_score)}`}>
              {report.code_quality_metrics.maintainability_score}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Test Coverage</p>
            <p className={`text-xl font-bold ${getScoreColor(report.code_quality_metrics.test_coverage_estimate)}`}>
              {report.code_quality_metrics.test_coverage_estimate}%
            </p>
          </div>
        </div>
      </Card>

      {/* Security Issues */}
      {report.security_issues.length > 0 && (
        <Card title="Security Issues" subtitle={`${report.security_issues.length} issue(s) found`}>
          <div className="space-y-3">
            {report.security_issues.map((issue, index) => (
              <SecurityIssueItem key={index} issue={issue} />
            ))}
          </div>
        </Card>
      )}

      {/* Optimization Suggestions */}
      {report.optimization_suggestions.length > 0 && (
        <Card title="Optimization Suggestions" subtitle={`${report.optimization_suggestions.length} suggestion(s)`}>
          <div className="space-y-3">
            {report.optimization_suggestions.map((suggestion, index) => (
              <OptimizationItem key={index} suggestion={suggestion} />
            ))}
          </div>
        </Card>
      )}

      {/* Vulnerability Assessment */}
      <Card title="Vulnerability Assessment">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Overall Risk Level:</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(report.vulnerability_assessment.overall_risk)}`}>
              {report.vulnerability_assessment.overall_risk}
            </span>
          </div>
          
          {report.vulnerability_assessment.detected_patterns.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">Detected Patterns:</h4>
              <ul className="space-y-1">
                {report.vulnerability_assessment.detected_patterns.map((pattern, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-center">
                    <CheckCircle className="h-4 w-4 mr-2 text-blue-500" />
                    {pattern}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {report.vulnerability_assessment.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">Recommendations:</h4>
              <ul className="space-y-1">
                {report.vulnerability_assessment.recommendations.map((recommendation, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-center">
                    <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                    {recommendation}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default AnalysisDisplay;
