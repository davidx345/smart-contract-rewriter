import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import api from '../../services/api';

interface SecurityAlert {
  id: number;
  alert_id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  threat_type: string;
  status: string;
  description: string;
  risk_score: number;
  detected_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

interface SecurityDashboard {
  active_alerts: number;
  critical_alerts: number;
  threats_blocked_today: number;
  average_response_time: number;
  top_threat_types: Array<{
    threat_type: string;
    count: number;
    percentage: number;
  }>;
  recent_alerts: SecurityAlert[];
}

interface ComplianceStatus {
  overall_score: number;
  gdpr_compliant: boolean;
  expired_data_count: number;
  last_assessment_date: string;
  recommendations: string[];
}

export const SecurityDashboard: React.FC = () => {
  const [dashboard, setDashboard] = useState<SecurityDashboard | null>(null);
  const [compliance, setCompliance] = useState<ComplianceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null);
  const [showAlertModal, setShowAlertModal] = useState(false);

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    try {
      const [dashboardResponse, complianceResponse] = await Promise.all([
        api.get('/security/dashboard'),
        api.get('/security/compliance-status')
      ]);

      setDashboard(dashboardResponse.data);
      setCompliance(complianceResponse.data);
      setLoading(false);
    } catch (err: any) {
      setError('Failed to load security data');
      setLoading(false);
    }
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await api.patch(`/security/alerts/${alertId}/acknowledge`);
      await loadSecurityData();
    } catch (err: any) {
      setError('Failed to acknowledge alert');
    }
  };

  const resolveAlert = async (alertId: string, notes: string, isFalsePositive: boolean = false) => {
    try {
      await api.patch(`/security/alerts/${alertId}/resolve`, {
        resolution_notes: notes,
        is_false_positive: isFalsePositive
      });
      await loadSecurityData();
      setShowAlertModal(false);
      setSelectedAlert(null);
    } catch (err: any) {
      setError('Failed to resolve alert');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-100 border-blue-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getComplianceColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Security & Compliance</h1>
          <p className="text-gray-600">Monitor security threats, alerts, and compliance status</p>
        </div>
        <Button onClick={() => window.location.reload()}>
          🔄 Refresh
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="p-4 border-red-200 bg-red-50">
          <div className="flex items-center space-x-2">
            <span className="text-red-600">⚠️</span>
            <span className="text-red-700">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </Card>
      )}

      {/* Security Metrics */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {dashboard.active_alerts}
              </div>
              <div className="text-sm text-gray-600 mt-1">Active Alerts</div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {dashboard.critical_alerts}
              </div>
              <div className="text-sm text-gray-600 mt-1">Critical Alerts</div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {dashboard.threats_blocked_today}
              </div>
              <div className="text-sm text-gray-600 mt-1">Threats Blocked Today</div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {dashboard.average_response_time.toFixed(1)}h
              </div>
              <div className="text-sm text-gray-600 mt-1">Avg Response Time</div>
            </div>
          </Card>
        </div>
      )}

      {/* Compliance Status */}
      {compliance && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Compliance Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className={`text-4xl font-bold ${getComplianceColor(compliance.overall_score)}`}>
                {compliance.overall_score.toFixed(0)}%
              </div>
              <div className="text-sm text-gray-600 mt-1">Overall Score</div>
            </div>
            
            <div className="text-center">
              <div className={`text-2xl font-semibold ${compliance.gdpr_compliant ? 'text-green-600' : 'text-red-600'}`}>
                {compliance.gdpr_compliant ? '✓ Compliant' : '✗ Non-Compliant'}
              </div>
              <div className="text-sm text-gray-600 mt-1">GDPR Status</div>
            </div>
            
            <div className="text-center">
              <div className={`text-2xl font-semibold ${compliance.expired_data_count === 0 ? 'text-green-600' : 'text-orange-600'}`}>
                {compliance.expired_data_count}
              </div>
              <div className="text-sm text-gray-600 mt-1">Expired Data Items</div>
            </div>
          </div>

          {compliance.recommendations.length > 0 && (
            <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-medium text-yellow-800 mb-2">Compliance Recommendations:</h4>
              <ul className="list-disc list-inside space-y-1">
                {compliance.recommendations.map((rec, index) => (
                  <li key={index} className="text-yellow-700 text-sm">{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}

      {/* Top Threats */}
      {dashboard && dashboard.top_threat_types.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Top Threat Types (Last 30 Days)</h3>
          <div className="space-y-3">
            {dashboard.top_threat_types.map((threat, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize">
                      {threat.threat_type.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-gray-600">
                      {threat.count} incidents ({threat.percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${threat.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recent Alerts */}
      {dashboard && dashboard.recent_alerts.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Security Alerts</h3>
          <div className="space-y-3">
            {dashboard.recent_alerts.map((alert) => (
              <div
                key={alert.id}
                className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                onClick={() => {
                  setSelectedAlert(alert);
                  setShowAlertModal(true);
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="font-medium">
                      {alert.threat_type.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      Risk: {alert.risk_score.toFixed(1)}/10
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      alert.status === 'open' ? 'bg-red-100 text-red-600' :
                      alert.status === 'investigating' ? 'bg-yellow-100 text-yellow-600' :
                      'bg-green-100 text-green-600'
                    }`}>
                      {alert.status}
                    </span>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-700">
                  {alert.description}
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  Detected: {new Date(alert.detected_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Alert Detail Modal */}
      {showAlertModal && selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Security Alert Details</h3>
              <button
                onClick={() => setShowAlertModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Alert ID</label>
                  <p className="text-sm">{selectedAlert.alert_id}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Severity</label>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(selectedAlert.severity)}`}>
                    {selectedAlert.severity.toUpperCase()}
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Threat Type</label>
                  <p className="text-sm">{selectedAlert.threat_type.replace('_', ' ')}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Risk Score</label>
                  <p className="text-sm">{selectedAlert.risk_score.toFixed(1)}/10</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <p className="text-sm mt-1">{selectedAlert.description}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Detected At</label>
                <p className="text-sm">{new Date(selectedAlert.detected_at).toLocaleString()}</p>
              </div>

              {selectedAlert.status === 'open' && (
                <div className="flex space-x-2">
                  <Button
                    onClick={() => acknowledgeAlert(selectedAlert.alert_id)}
                    variant="outline"
                    className="flex-1"
                  >
                    Acknowledge
                  </Button>
                  <Button
                    onClick={() => resolveAlert(selectedAlert.alert_id, 'Resolved by security team', false)}
                    className="flex-1"
                  >
                    Resolve
                  </Button>
                  <Button
                    onClick={() => resolveAlert(selectedAlert.alert_id, 'Marked as false positive', true)}
                    variant="outline"
                    className="flex-1"
                  >
                    False Positive
                  </Button>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
