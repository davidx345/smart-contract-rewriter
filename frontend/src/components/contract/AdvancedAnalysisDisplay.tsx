import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Spinner from '../ui/Spinner';
import api from '../../services/api';

interface VulnerabilityDetection {
  severity: string;
  type: string;
  description: string;
  line_numbers: number[];
  recommendation: string;
  confidence: number;
}

interface GasOptimization {
  current_estimate: number;
  optimized_estimate: number;
  savings_percentage: number;
  optimizations: string[];
  code_changes: Array<{
    line: string;
    original: string;
    optimized: string;
  }>;
}

interface ContractCompliance {
  standard: string;
  compliance_score: number;
  missing_functions: string[];
  recommendations: string[];
}

interface SmartContractMetrics {
  complexity_score: number;
  maintainability_index: number;
  test_coverage_estimate: number;
  security_score: number;
  deployment_cost_estimate: number;
}

interface AdvancedAnalysisResponse {
  analysis_id: string;
  timestamp: string;
  contract_hash: string;
  vulnerabilities: VulnerabilityDetection[];
  gas_optimization?: GasOptimization;
  compliance?: ContractCompliance;
  metrics?: SmartContractMetrics;
  overall_score: number;
  recommendations: string[];
  risk_level: string;
  processing_time: number;
  ai_model_version: string;
}

interface AdvancedAnalysisDisplayProps {
  contractCode: string;
  onAnalysisComplete?: (analysis: AdvancedAnalysisResponse) => void;
}

export const AdvancedAnalysisDisplay: React.FC<AdvancedAnalysisDisplayProps> = ({
  contractCode,
  onAnalysisComplete
}) => {
  const [analysis, setAnalysis] = useState<AdvancedAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisType, setAnalysisType] = useState('comprehensive');
  const [selectedTab, setSelectedTab] = useState('overview');

  const runAdvancedAnalysis = async () => {
    if (!contractCode.trim()) {
      setError('Please provide contract code to analyze');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/ai/analyze/advanced', {
        contract_code: contractCode,
        analysis_type: analysisType,
        target_network: 'ethereum',
        include_suggestions: true
      });

      setAnalysis(response.data);
      onAnalysisComplete?.(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Advanced analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatProcessingTime = (seconds: number) => {
    return seconds < 1 ? `${(seconds * 1000).toFixed(0)}ms` : `${seconds.toFixed(2)}s`;
  };

  const ScoreIndicator: React.FC<{ score: number; max: number; label: string; color?: string }> = ({
    score,
    max,
    label,
    color = 'blue'
  }) => {
    const percentage = (score / max) * 100;
    
    return (
      <div className="flex items-center space-x-3">
        <div className="flex-1">
          <div className="flex justify-between text-sm mb-1">
            <span className="font-medium">{label}</span>
            <span>{score.toFixed(1)}/{max}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`bg-${color}-600 h-2 rounded-full transition-all duration-300`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Analysis Controls */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Advanced AI Analysis</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Analysis Type</label>
            <select
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="comprehensive">Comprehensive Analysis</option>
              <option value="vulnerability">Security Vulnerabilities</option>
              <option value="gas">Gas Optimization</option>
              <option value="compliance">Standard Compliance</option>
              <option value="metrics">Code Quality Metrics</option>
            </select>
          </div>

          <Button
            onClick={runAdvancedAnalysis}
            disabled={loading || !contractCode.trim()}
            className="w-full"
          >
            {loading ? (
              <>
                <Spinner className="w-4 h-4 mr-2" />
                Analyzing Contract...
              </>
            ) : (
              'Run Advanced Analysis'
            )}
          </Button>
        </div>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="p-4 border-red-200 bg-red-50">
          <div className="flex items-center space-x-2">
            <span className="text-red-600">Warning</span>
            <span className="text-red-700">{error}</span>
          </div>
        </Card>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-6">
          {/* Overview */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Analysis Overview</h3>
              <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskLevelColor(analysis.risk_level)}`}>
                Risk Level: {analysis.risk_level}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{analysis.overall_score.toFixed(1)}</div>
                <div className="text-sm text-blue-600">Overall Score</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{analysis.vulnerabilities.length}</div>
                <div className="text-sm text-purple-600">Vulnerabilities</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{formatProcessingTime(analysis.processing_time)}</div>
                <div className="text-sm text-green-600">Processing Time</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">{analysis.ai_model_version}</div>
                <div className="text-sm text-orange-600">AI Model</div>
              </div>
            </div>

            <div className="text-xs text-gray-500 space-y-1">
              <div>Analysis ID: {analysis.analysis_id}</div>
              <div>Contract Hash: {analysis.contract_hash.substring(0, 16)}...</div>
              <div>Timestamp: {new Date(analysis.timestamp).toLocaleString()}</div>
            </div>
          </Card>

          {/* Tabbed Interface */}
          <Card className="p-6">
            <div className="flex space-x-4 mb-6 border-b">
              {[
                { id: 'vulnerabilities', label: 'Security', count: analysis.vulnerabilities.length },
                { id: 'gas', label: '⛽ Gas Optimization', enabled: !!analysis.gas_optimization },
                { id: 'compliance', label: 'Compliance', enabled: !!analysis.compliance },
                { id: 'metrics', label: 'Metrics', enabled: !!analysis.metrics },
                { id: 'recommendations', label: 'Recommendations', count: analysis.recommendations.length }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id)}
                  disabled={tab.enabled === false}
                  className={`px-4 py-2 font-medium text-sm rounded-t-lg border-b-2 ${
                    selectedTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  } ${tab.enabled === false ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {tab.label}
                  {tab.count !== undefined && (
                    <span className="ml-2 px-2 py-1 text-xs bg-gray-200 rounded-full">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="space-y-4">
              {selectedTab === 'vulnerabilities' && (
                <div className="space-y-4">
                  {analysis.vulnerabilities.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      No vulnerabilities detected
                    </div>
                  ) : (
                    analysis.vulnerabilities.map((vuln, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold">{vuln.type}</h4>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(vuln.severity)}`}>
                              {vuln.severity}
                            </span>
                            <span className="text-xs text-gray-500">
                              {(vuln.confidence * 100).toFixed(0)}% confidence
                            </span>
                          </div>
                        </div>
                        <p className="text-gray-700 mb-2">{vuln.description}</p>
                        <div className="text-sm text-gray-600 mb-2">
                          <strong>Recommendation:</strong> {vuln.recommendation}
                        </div>
                        {vuln.line_numbers.length > 0 && (
                          <div className="text-xs text-gray-500">
                            Lines: {vuln.line_numbers.join(', ')}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {selectedTab === 'gas' && analysis.gas_optimization && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-lg font-bold text-red-600">
                        {analysis.gas_optimization.current_estimate.toLocaleString()}
                      </div>
                      <div className="text-sm text-red-600">Current Estimate</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-lg font-bold text-green-600">
                        {analysis.gas_optimization.optimized_estimate.toLocaleString()}
                      </div>
                      <div className="text-sm text-green-600">Optimized Estimate</div>
                    </div>
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-lg font-bold text-blue-600">
                        -{analysis.gas_optimization.savings_percentage.toFixed(1)}%
                      </div>
                      <div className="text-sm text-blue-600">Savings</div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold mb-2">Optimization Suggestions:</h4>
                    <ul className="space-y-1">
                      {analysis.gas_optimization.optimizations.map((opt, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="text-green-500">✓</span>
                          <span className="text-sm">{opt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {analysis.gas_optimization.code_changes.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Code Changes:</h4>
                      <div className="space-y-2">
                        {analysis.gas_optimization.code_changes.map((change, index) => (
                          <div key={index} className="border rounded p-3 text-sm">
                            <div className="text-gray-600 mb-1">Line {change.line}:</div>
                            <div className="bg-red-50 p-2 rounded mb-1">
                              <span className="text-red-600">- </span>
                              <code className="text-red-800">{change.original}</code>
                            </div>
                            <div className="bg-green-50 p-2 rounded">
                              <span className="text-green-600">+ </span>
                              <code className="text-green-800">{change.optimized}</code>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {selectedTab === 'compliance' && analysis.compliance && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold">Standard: {analysis.compliance.standard}</h4>
                      <div className="mt-2">
                        <ScoreIndicator
                          score={analysis.compliance.compliance_score * 10}
                          max={10}
                          label="Compliance Score"
                          color="green"
                        />
                      </div>
                    </div>
                  </div>

                  {analysis.compliance.missing_functions.length > 0 && (
                    <div>
                      <h5 className="font-medium mb-2">Missing Functions:</h5>
                      <div className="flex flex-wrap gap-2">
                        {analysis.compliance.missing_functions.map((func, index) => (
                          <span key={index} className="px-2 py-1 bg-red-100 text-red-800 rounded text-sm">
                            {func}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {analysis.compliance.recommendations.length > 0 && (
                    <div>
                      <h5 className="font-medium mb-2">Recommendations:</h5>
                      <ul className="space-y-1">
                        {analysis.compliance.recommendations.map((rec, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <span className="text-blue-500">Tip</span>
                            <span className="text-sm">{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {selectedTab === 'metrics' && analysis.metrics && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <ScoreIndicator
                        score={analysis.metrics.complexity_score}
                        max={10}
                        label="Complexity Score"
                        color="yellow"
                      />
                      <ScoreIndicator
                        score={analysis.metrics.maintainability_index}
                        max={100}
                        label="Maintainability Index"
                        color="blue"
                      />
                    </div>
                    <div className="space-y-4">
                      <ScoreIndicator
                        score={analysis.metrics.security_score}
                        max={10}
                        label="Security Score"
                        color="green"
                      />
                      <ScoreIndicator
                        score={analysis.metrics.test_coverage_estimate * 100}
                        max={100}
                        label="Est. Test Coverage"
                        color="purple"
                      />
                    </div>
                  </div>

                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h5 className="font-medium mb-2">Deployment Cost Estimate</h5>
                    <div className="text-2xl font-bold text-gray-700">
                      {analysis.metrics.deployment_cost_estimate.toLocaleString()} gas
                    </div>
                    <div className="text-sm text-gray-500">
                      ≈ ${((analysis.metrics.deployment_cost_estimate * 20) / 1e9).toFixed(2)} USD
                      <span className="ml-1">(@ 20 gwei)</span>
                    </div>
                  </div>
                </div>
              )}

              {selectedTab === 'recommendations' && (
                <div className="space-y-3">
                  {analysis.recommendations.map((rec, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                      <span className="text-blue-500 mt-0.5">Tip</span>
                      <span className="text-blue-800">{rec}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
