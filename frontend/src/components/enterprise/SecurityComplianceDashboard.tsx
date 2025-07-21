import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import api from '../../services/api';

interface AuditLog {
  id: number;
  organization_id: number;
  user_id: number;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address: string;
  user_agent: string;
  timestamp: string;
}

interface SecuritySettings {
  two_factor_required: boolean;
  session_timeout_minutes: number;
  allowed_ip_ranges: string[];
  sso_enabled: boolean;
  password_policy: {
    min_length: number;
    require_uppercase: boolean;
    require_lowercase: boolean;
    require_numbers: boolean;
    require_symbols: boolean;
    max_age_days: number;
  };
  api_rate_limits: {
    per_minute: number;
    per_hour: number;
    per_day: number;
  };
}

interface ComplianceReport {
  id: number;
  report_type: string;
  period_start: string;
  period_end: string;
  status: 'generating' | 'ready' | 'failed';
  file_url?: string;
  created_at: string;
}

export const SecurityComplianceDashboard: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [settings, setSettings] = useState<SecuritySettings | null>(null);
  const [reports, setReports] = useState<ComplianceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('audit');

  // Filters for audit logs
  const [dateRange, setDateRange] = useState('7d');
  const [actionFilter, setActionFilter] = useState('all');
  const [userFilter, setUserFilter] = useState('');

  // Settings update
  const [updatingSettings, setUpdatingSettings] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Report generation
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportType, setReportType] = useState('audit');

  useEffect(() => {
    loadData();
  }, [dateRange, actionFilter, userFilter]);

  const loadData = async () => {
    try {
      const params = new URLSearchParams({
        range: dateRange,
        ...(actionFilter !== 'all' && { action: actionFilter }),
        ...(userFilter && { user: userFilter })
      });

      const [logsResponse, settingsResponse, reportsResponse] = await Promise.all([
        api.get(`/enterprise/audit-logs?${params}`),
        api.get('/enterprise/security-settings'),
        api.get('/enterprise/compliance-reports')
      ]);

      setAuditLogs(logsResponse.data);
      setSettings(settingsResponse.data);
      setReports(reportsResponse.data);
      setLoading(false);
    } catch (err: any) {
      setError('Failed to load security data');
      setLoading(false);
    }
  };

  const updateSettings = async (newSettings: Partial<SecuritySettings>) => {
    setUpdatingSettings(true);
    try {
      const response = await api.put('/enterprise/security-settings', newSettings);
      setSettings(response.data);
      setShowSettingsModal(false);
    } catch (err: any) {
      setError('Failed to update security settings');
    } finally {
      setUpdatingSettings(false);
    }
  };

  const generateReport = async () => {
    setGeneratingReport(true);
    try {
      const response = await api.post('/enterprise/compliance-reports', {
        report_type: reportType,
        period_start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        period_end: new Date().toISOString()
      });
      
      setReports([response.data, ...reports]);
    } catch (err: any) {
      setError('Failed to generate compliance report');
    } finally {
      setGeneratingReport(false);
    }
  };

  const downloadReport = async (reportId: number) => {
    try {
      const response = await api.get(`/enterprise/compliance-reports/${reportId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `compliance-report-${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download report');
    }
  };

  const getActionColor = (action: string) => {
    if (action.includes('login') || action.includes('auth')) return 'text-blue-600 bg-blue-100';
    if (action.includes('create') || action.includes('add')) return 'text-green-600 bg-green-100';
    if (action.includes('delete') || action.includes('remove')) return 'text-red-600 bg-red-100';
    if (action.includes('update') || action.includes('modify')) return 'text-yellow-600 bg-yellow-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'text-green-600 bg-green-100';
      case 'generating': return 'text-yellow-600 bg-yellow-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
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
          <p className="text-gray-600">Monitor security events and manage compliance requirements</p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setShowSettingsModal(true)} variant="outline">
            Security Settings
          </Button>
          <Button onClick={generateReport} disabled={generatingReport}>
            {generatingReport ? 'Generating...' : 'Generate Report'}
          </Button>
        </div>
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

      {/* Security Overview */}
      {settings && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="p-6">
            <h3 className="text-sm font-medium text-gray-500">Two-Factor Auth</h3>
            <div className="mt-2 flex items-center">
              <span className={`px-2 py-1 text-sm font-medium rounded ${
                settings.two_factor_required 
                  ? 'text-green-600 bg-green-100' 
                  : 'text-red-600 bg-red-100'
              }`}>
                {settings.two_factor_required ? 'Required' : 'Optional'}
              </span>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-medium text-gray-500">Session Timeout</h3>
            <div className="mt-2 text-2xl font-semibold text-gray-900">
              {settings.session_timeout_minutes}m
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-medium text-gray-500">SSO</h3>
            <div className="mt-2 flex items-center">
              <span className={`px-2 py-1 text-sm font-medium rounded ${
                settings.sso_enabled 
                  ? 'text-green-600 bg-green-100' 
                  : 'text-gray-600 bg-gray-100'
              }`}>
                {settings.sso_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-medium text-gray-500">IP Restrictions</h3>
            <div className="mt-2 text-2xl font-semibold text-gray-900">
              {settings.allowed_ip_ranges.length}
            </div>
            <div className="text-sm text-gray-500">ranges configured</div>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Card className="p-4">
        <div className="flex space-x-4 border-b">
          {[
            { id: 'audit', label: '📋 Audit Logs', count: auditLogs.length },
            { id: 'reports', label: '📊 Compliance Reports', count: reports.length },
            { id: 'alerts', label: '🚨 Security Alerts' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 font-medium text-sm rounded-t-lg border-b-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
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
      </Card>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Audit Logs Tab */}
        {activeTab === 'audit' && (
          <div className="space-y-4">
            {/* Filters */}
            <Card className="p-4">
              <div className="flex flex-wrap gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Time Range</label>
                  <select
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="1d">Last 24 hours</option>
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                    <option value="90d">Last 90 days</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Action</label>
                  <select
                    value={actionFilter}
                    onChange={(e) => setActionFilter(e.target.value)}
                    className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Actions</option>
                    <option value="login">Login Events</option>
                    <option value="create">Create Actions</option>
                    <option value="update">Update Actions</option>
                    <option value="delete">Delete Actions</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">User</label>
                  <input
                    type="text"
                    value={userFilter}
                    onChange={(e) => setUserFilter(e.target.value)}
                    placeholder="Filter by email"
                    className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </Card>

            {/* Audit Logs Table */}
            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Resource
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        IP Address
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Details
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {auditLogs.map(log => (
                      <tr key={log.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {log.user_email}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getActionColor(log.action)}`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {log.resource_type}
                          {log.resource_id && (
                            <div className="text-xs text-gray-400">#{log.resource_id}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                          {log.ip_address}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          <button className="text-blue-600 hover:text-blue-900">
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {auditLogs.length === 0 && (
                <div className="p-6 text-center text-gray-500">
                  No audit logs found for the selected filters
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Compliance Reports Tab */}
        {activeTab === 'reports' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Compliance Reports</h3>
              <div className="flex space-x-2">
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="audit">Audit Report</option>
                  <option value="security">Security Report</option>
                  <option value="compliance">Compliance Report</option>
                  <option value="data-protection">Data Protection Report</option>
                </select>
                <Button onClick={generateReport} disabled={generatingReport}>
                  {generatingReport ? 'Generating...' : 'Generate Report'}
                </Button>
              </div>
            </div>

            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Report Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Period
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Generated
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reports.map(report => (
                      <tr key={report.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {report.report_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(report.period_start).toLocaleDateString()} - {new Date(report.period_end).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(report.status)}`}>
                            {report.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(report.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {report.status === 'ready' && (
                            <button
                              onClick={() => downloadReport(report.id)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              Download
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {reports.length === 0 && (
                <div className="p-6 text-center text-gray-500">
                  No compliance reports generated yet
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Security Alerts Tab */}
        {activeTab === 'alerts' && (
          <div className="space-y-4">
            <Card className="p-6 text-center text-gray-500">
              <div className="text-4xl mb-4">🚨</div>
              <h3 className="text-lg font-medium mb-2">Security Alert System</h3>
              <p>Real-time security monitoring and alerting system would be implemented here.</p>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
                <div className="p-4 bg-gray-50 rounded">
                  <h4 className="font-medium">Failed Login Attempts</h4>
                  <p className="text-sm">Monitor and alert on suspicious login patterns</p>
                </div>
                <div className="p-4 bg-gray-50 rounded">
                  <h4 className="font-medium">API Rate Limiting</h4>
                  <p className="text-sm">Alert when rate limits are exceeded</p>
                </div>
                <div className="p-4 bg-gray-50 rounded">
                  <h4 className="font-medium">Data Access Patterns</h4>
                  <p className="text-sm">Monitor unusual data access patterns</p>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* Security Settings Modal */}
      {showSettingsModal && settings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Security Settings</h3>
            
            <div className="space-y-6">
              {/* Two-Factor Authentication */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.two_factor_required}
                    onChange={(e) => setSettings({
                      ...settings,
                      two_factor_required: e.target.checked
                    })}
                    className="mr-2"
                  />
                  <span className="font-medium">Require Two-Factor Authentication</span>
                </label>
                <p className="text-sm text-gray-600 mt-1">
                  All users must enable 2FA to access the organization
                </p>
              </div>

              {/* Session Timeout */}
              <div>
                <label className="block font-medium mb-2">Session Timeout (minutes)</label>
                <input
                  type="number"
                  value={settings.session_timeout_minutes}
                  onChange={(e) => setSettings({
                    ...settings,
                    session_timeout_minutes: parseInt(e.target.value) || 60
                  })}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  min="5"
                  max="1440"
                />
              </div>

              {/* SSO */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.sso_enabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      sso_enabled: e.target.checked
                    })}
                    className="mr-2"
                  />
                  <span className="font-medium">Enable Single Sign-On (SSO)</span>
                </label>
              </div>

              {/* Password Policy */}
              <div>
                <h4 className="font-medium mb-2">Password Policy</h4>
                <div className="space-y-2 text-sm">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.password_policy.require_uppercase}
                      onChange={(e) => setSettings({
                        ...settings,
                        password_policy: {
                          ...settings.password_policy,
                          require_uppercase: e.target.checked
                        }
                      })}
                      className="mr-2"
                    />
                    Require uppercase letters
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.password_policy.require_numbers}
                      onChange={(e) => setSettings({
                        ...settings,
                        password_policy: {
                          ...settings.password_policy,
                          require_numbers: e.target.checked
                        }
                      })}
                      className="mr-2"
                    />
                    Require numbers
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.password_policy.require_symbols}
                      onChange={(e) => setSettings({
                        ...settings,
                        password_policy: {
                          ...settings.password_policy,
                          require_symbols: e.target.checked
                        }
                      })}
                      className="mr-2"
                    />
                    Require symbols
                  </label>
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={() => updateSettings(settings)}
                  disabled={updatingSettings}
                  className="flex-1"
                >
                  {updatingSettings ? 'Updating...' : 'Save Settings'}
                </Button>
                <Button
                  onClick={() => setShowSettingsModal(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
