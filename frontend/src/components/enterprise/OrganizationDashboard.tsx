import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Spinner from '../ui/Spinner';
import api from '../../services/api';

interface Organization {
  id: number;
  name: string;
  slug: string;
  subscription_tier: string;
  monthly_contract_limit: number;
  monthly_ai_analysis_limit: number;
  monthly_api_calls_limit: number;
  storage_limit_mb: number;
  custom_branding: boolean;
  sso_enabled: boolean;
  audit_logging: boolean;
  priority_support: boolean;
  created_at: string;
}

interface OrganizationMember {
  id: number;
  user_id: number;
  user_email: string;
  user_name: string;
  role: string;
  can_manage_members: boolean;
  can_manage_billing: boolean;
  can_manage_api_keys: boolean;
  can_view_usage: boolean;
  can_create_contracts: boolean;
  joined_at: string;
  last_active_at?: string;
}

interface APIKey {
  id: number;
  name: string;
  key_prefix: string;
  key_type: string;
  rate_limit_per_minute: number;
  rate_limit_per_hour: number;
  rate_limit_per_day: number;
  is_active: boolean;
  total_calls: number;
  last_used_at?: string;
  expires_at?: string;
  created_at: string;
}

interface UsageAnalytics {
  total_contract_analyses: number;
  total_ai_analyses: number;
  total_api_calls: number;
  total_storage_used_mb: number;
  current_month_usage: Record<string, number>;
  daily_usage_trend: Array<{ date: string; count: number }>;
  top_endpoints: Array<{ endpoint: string; count: number }>;
}

export const OrganizationDashboard: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [usage, setUsage] = useState<UsageAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // New organization form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgDescription, setNewOrgDescription] = useState('');
  const [creating, setCreating] = useState(false);

  // Invite member form
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviting, setInviting] = useState(false);

  // API key form
  const [showApiKeyForm, setShowApiKeyForm] = useState(false);
  const [newApiKeyName, setNewApiKeyName] = useState('');
  const [newApiKeyType, setNewApiKeyType] = useState('read_write');
  const [creatingApiKey, setCreatingApiKey] = useState(false);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrg) {
      loadOrganizationData();
    }
  }, [selectedOrg]);

  const loadOrganizations = async () => {
    try {
      const response = await api.get('/enterprise/organizations');
      setOrganizations(response.data);
      if (response.data.length > 0 && !selectedOrg) {
        setSelectedOrg(response.data[0]);
      }
      setLoading(false);
    } catch (err: any) {
      setError('Failed to load organizations');
      setLoading(false);
    }
  };

  const loadOrganizationData = async () => {
    if (!selectedOrg) return;

    try {
      const [membersResponse, apiKeysResponse, usageResponse] = await Promise.all([
        api.get(`/enterprise/organizations/${selectedOrg.slug}/members`),
        api.get(`/enterprise/organizations/${selectedOrg.slug}/api-keys`),
        api.get(`/enterprise/organizations/${selectedOrg.slug}/analytics`)
      ]);

      setMembers(membersResponse.data);
      setApiKeys(apiKeysResponse.data);
      setUsage(usageResponse.data);
    } catch (err: any) {
      setError('Failed to load organization data');
    }
  };

  const createOrganization = async () => {
    if (!newOrgName.trim()) return;

    setCreating(true);
    try {
      const response = await api.post('/enterprise/organizations', {
        name: newOrgName,
        description: newOrgDescription
      });

      setOrganizations([...organizations, response.data]);
      setSelectedOrg(response.data);
      setShowCreateForm(false);
      setNewOrgName('');
      setNewOrgDescription('');
    } catch (err: any) {
      setError('Failed to create organization');
    } finally {
      setCreating(false);
    }
  };

  const inviteMember = async () => {
    if (!inviteEmail.trim() || !selectedOrg) return;

    setInviting(true);
    try {
      await api.post(`/enterprise/organizations/${selectedOrg.slug}/members`, {
        email: inviteEmail,
        role: inviteRole,
        can_manage_members: inviteRole === 'admin',
        can_manage_billing: inviteRole === 'admin',
        can_manage_api_keys: inviteRole === 'admin',
        can_view_usage: true,
        can_create_contracts: true
      });

      await loadOrganizationData();
      setShowInviteForm(false);
      setInviteEmail('');
      setInviteRole('member');
    } catch (err: any) {
      setError('Failed to invite member');
    } finally {
      setInviting(false);
    }
  };

  const createApiKey = async () => {
    if (!newApiKeyName.trim() || !selectedOrg) return;

    setCreatingApiKey(true);
    try {
      const response = await api.post(`/enterprise/organizations/${selectedOrg.slug}/api-keys`, {
        name: newApiKeyName,
        key_type: newApiKeyType,
        rate_limit_per_minute: 60,
        rate_limit_per_hour: 1000,
        rate_limit_per_day: 10000
      });

      setNewApiKey(response.data.api_key);
      await loadOrganizationData();
      setShowApiKeyForm(false);
      setNewApiKeyName('');
      setNewApiKeyType('read_write');
    } catch (err: any) {
      setError('Failed to create API key');
    } finally {
      setCreatingApiKey(false);
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'free': return 'text-gray-600 bg-gray-100';
      case 'starter': return 'text-blue-600 bg-blue-100';
      case 'professional': return 'text-purple-600 bg-purple-100';
      case 'enterprise': return 'text-gold-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'owner': return 'text-red-600 bg-red-100';
      case 'admin': return 'text-purple-600 bg-purple-100';
      case 'member': return 'text-blue-600 bg-blue-100';
      case 'viewer': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
          <p className="text-gray-600">Manage your teams, billing, and enterprise features</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          + Create Organization
        </Button>
      </div>

      {/* Organization Selector */}
      {organizations.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center space-x-4">
            <label className="font-medium">Organization:</label>
            <select
              value={selectedOrg?.id || ''}
              onChange={(e) => {
                const org = organizations.find(o => o.id === parseInt(e.target.value));
                setSelectedOrg(org || null);
              }}
              className="flex-1 max-w-md p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              {organizations.map(org => (
                <option key={org.id} value={org.id}>
                  {org.name} ({org.slug})
                </option>
              ))}
            </select>
            {selectedOrg && (
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTierColor(selectedOrg.subscription_tier)}`}>
                {selectedOrg.subscription_tier.toUpperCase()}
              </span>
            )}
          </div>
        </Card>
      )}

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

      {/* Main Content */}
      {selectedOrg && (
        <div className="space-y-6">
          {/* Tabs */}
          <Card className="p-4">
            <div className="flex space-x-4 border-b">
              {[
                { id: 'overview', label: '📊 Overview' },
                { id: 'members', label: '👥 Team', count: members.length },
                { id: 'api-keys', label: '🔑 API Keys', count: apiKeys.length },
                { id: 'usage', label: '📈 Usage' },
                { id: 'billing', label: '💳 Billing' },
                { id: 'settings', label: '⚙️ Settings' }
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
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="p-6">
                  <h3 className="text-sm font-medium text-gray-500">Contract Analyses</h3>
                  <div className="mt-2 flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {usage?.current_month_usage?.contract_analysis || 0}
                    </div>
                    <div className="ml-2 text-sm text-gray-500">
                      / {selectedOrg.monthly_contract_limit === -1 ? '∞' : selectedOrg.monthly_contract_limit}
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <h3 className="text-sm font-medium text-gray-500">AI Analyses</h3>
                  <div className="mt-2 flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {usage?.current_month_usage?.ai_analysis || 0}
                    </div>
                    <div className="ml-2 text-sm text-gray-500">
                      / {selectedOrg.monthly_ai_analysis_limit === -1 ? '∞' : selectedOrg.monthly_ai_analysis_limit}
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <h3 className="text-sm font-medium text-gray-500">API Calls</h3>
                  <div className="mt-2 flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {usage?.current_month_usage?.api_call || 0}
                    </div>
                    <div className="ml-2 text-sm text-gray-500">
                      / {selectedOrg.monthly_api_calls_limit === -1 ? '∞' : selectedOrg.monthly_api_calls_limit}
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <h3 className="text-sm font-medium text-gray-500">Team Members</h3>
                  <div className="mt-2 flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {members.length}
                    </div>
                    <div className="ml-2 text-sm text-gray-500">
                      active
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* Team Tab */}
            {activeTab === 'members' && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold">Team Members</h3>
                  <Button onClick={() => setShowInviteForm(true)}>
                    + Invite Member
                  </Button>
                </div>

                <Card className="overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Member
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Role
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Joined
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Last Active
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {members.map(member => (
                          <tr key={member.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div>
                                <div className="text-sm font-medium text-gray-900">
                                  {member.user_name}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {member.user_email}
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleColor(member.role)}`}>
                                {member.role}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(member.joined_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {member.last_active_at 
                                ? new Date(member.last_active_at).toLocaleDateString()
                                : 'Never'
                              }
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {member.role !== 'owner' && (
                                <button className="text-red-600 hover:text-red-900">
                                  Remove
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </div>
            )}

            {/* API Keys Tab */}
            {activeTab === 'api-keys' && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold">API Keys</h3>
                  <Button onClick={() => setShowApiKeyForm(true)}>
                    + Create API Key
                  </Button>
                </div>

                <Card className="overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Name
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Key
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Usage
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {apiKeys.map(key => (
                          <tr key={key.id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {key.name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                              {key.key_prefix}...
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {key.key_type.replace('_', ' ')}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {key.total_calls} calls
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                key.is_active 
                                  ? 'text-green-600 bg-green-100' 
                                  : 'text-red-600 bg-red-100'
                              }`}>
                                {key.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <button className="text-red-600 hover:text-red-900">
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </div>
            )}

            {/* Usage Tab */}
            {activeTab === 'usage' && usage && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">Usage Analytics</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Card className="p-6">
                    <h4 className="text-sm font-medium text-gray-500">Total Contract Analyses</h4>
                    <div className="text-2xl font-semibold text-gray-900 mt-2">
                      {usage.total_contract_analyses.toLocaleString()}
                    </div>
                  </Card>
                  
                  <Card className="p-6">
                    <h4 className="text-sm font-medium text-gray-500">Total AI Analyses</h4>
                    <div className="text-2xl font-semibold text-gray-900 mt-2">
                      {usage.total_ai_analyses.toLocaleString()}
                    </div>
                  </Card>
                  
                  <Card className="p-6">
                    <h4 className="text-sm font-medium text-gray-500">Total API Calls</h4>
                    <div className="text-2xl font-semibold text-gray-900 mt-2">
                      {usage.total_api_calls.toLocaleString()}
                    </div>
                  </Card>
                </div>

                {/* Top Endpoints */}
                {usage.top_endpoints.length > 0 && (
                  <Card className="p-6">
                    <h4 className="text-lg font-semibold mb-4">Top Endpoints</h4>
                    <div className="space-y-2">
                      {usage.top_endpoints.map((endpoint, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm text-gray-700 font-mono">
                            {endpoint.endpoint}
                          </span>
                          <span className="text-sm font-medium">
                            {endpoint.count} calls
                          </span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Organization Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Create Organization</h3>
            <div className="space-y-4">
              <Input
                value={newOrgName}
                onChange={(e) => setNewOrgName(e.target.value)}
                placeholder="Organization name"
                className="w-full"
              />
              <textarea
                value={newOrgDescription}
                onChange={(e) => setNewOrgDescription(e.target.value)}
                placeholder="Description (optional)"
                rows={3}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex space-x-2">
                <Button
                  onClick={createOrganization}
                  disabled={creating || !newOrgName.trim()}
                  className="flex-1"
                >
                  {creating ? <Spinner className="w-4 h-4 mr-2" /> : null}
                  Create
                </Button>
                <Button
                  onClick={() => setShowCreateForm(false)}
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

      {/* Invite Member Modal */}
      {showInviteForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Invite Team Member</h3>
            <div className="space-y-4">
              <Input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="Email address"
                className="w-full"
              />
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="viewer">Viewer</option>
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
              <div className="flex space-x-2">
                <Button
                  onClick={inviteMember}
                  disabled={inviting || !inviteEmail.trim()}
                  className="flex-1"
                >
                  {inviting ? <Spinner className="w-4 h-4 mr-2" /> : null}
                  Invite
                </Button>
                <Button
                  onClick={() => setShowInviteForm(false)}
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

      {/* Create API Key Modal */}
      {showApiKeyForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Create API Key</h3>
            <div className="space-y-4">
              <Input
                value={newApiKeyName}
                onChange={(e) => setNewApiKeyName(e.target.value)}
                placeholder="API key name"
                className="w-full"
              />
              <select
                value={newApiKeyType}
                onChange={(e) => setNewApiKeyType(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="read_only">Read Only</option>
                <option value="read_write">Read & Write</option>
                <option value="admin">Admin</option>
              </select>
              <div className="flex space-x-2">
                <Button
                  onClick={createApiKey}
                  disabled={creatingApiKey || !newApiKeyName.trim()}
                  className="flex-1"
                >
                  {creatingApiKey ? <Spinner className="w-4 h-4 mr-2" /> : null}
                  Create
                </Button>
                <Button
                  onClick={() => setShowApiKeyForm(false)}
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

      {/* New API Key Display Modal */}
      {newApiKey && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">API Key Created</h3>
            <div className="space-y-4">
              <div className="p-3 bg-gray-100 rounded-md">
                <p className="text-sm text-gray-600 mb-2">
                  Copy this API key now. It won't be shown again.
                </p>
                <code className="text-sm font-mono break-all">
                  {newApiKey}
                </code>
              </div>
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(newApiKey);
                  setNewApiKey(null);
                }}
                className="w-full"
              >
                Copy & Close
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
