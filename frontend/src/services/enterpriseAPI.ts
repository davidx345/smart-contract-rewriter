import api from './api';

// Organization Types
export interface Organization {
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

export interface OrganizationMember {
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

export interface APIKey {
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

export interface UsageAnalytics {
  total_contract_analyses: number;
  total_ai_analyses: number;
  total_api_calls: number;
  total_storage_used_mb: number;
  current_month_usage: Record<string, number>;
  daily_usage_trend: Array<{ date: string; count: number }>;
  top_endpoints: Array<{ endpoint: string; count: number }>;
}

// Enterprise API Service
export class EnterpriseAPIService {
  // Organization Management
  static async getOrganizations(): Promise<Organization[]> {
    const response = await api.get('/enterprise/organizations');
    return response.data;
  }

  static async createOrganization(data: { name: string; description?: string }): Promise<Organization> {
    const response = await api.post('/enterprise/organizations', data);
    return response.data;
  }

  static async updateOrganization(slug: string, data: Partial<Organization>): Promise<Organization> {
    const response = await api.put(`/enterprise/organizations/${slug}`, data);
    return response.data;
  }

  static async deleteOrganization(slug: string): Promise<void> {
    await api.delete(`/enterprise/organizations/${slug}`);
  }

  // Team Management
  static async getMembers(orgSlug: string): Promise<OrganizationMember[]> {
    const response = await api.get(`/enterprise/organizations/${orgSlug}/members`);
    return response.data;
  }

  static async inviteMember(orgSlug: string, data: {
    email: string;
    role: string;
    can_manage_members?: boolean;
    can_manage_billing?: boolean;
    can_manage_api_keys?: boolean;
    can_view_usage?: boolean;
    can_create_contracts?: boolean;
  }): Promise<OrganizationMember> {
    const response = await api.post(`/enterprise/organizations/${orgSlug}/members`, data);
    return response.data;
  }

  static async updateMember(orgSlug: string, memberId: number, data: Partial<OrganizationMember>): Promise<OrganizationMember> {
    const response = await api.put(`/enterprise/organizations/${orgSlug}/members/${memberId}`, data);
    return response.data;
  }

  static async removeMember(orgSlug: string, memberId: number): Promise<void> {
    await api.delete(`/enterprise/organizations/${orgSlug}/members/${memberId}`);
  }

  // API Key Management
  static async getAPIKeys(orgSlug: string): Promise<APIKey[]> {
    const response = await api.get(`/enterprise/organizations/${orgSlug}/api-keys`);
    return response.data;
  }

  static async createAPIKey(orgSlug: string, data: {
    name: string;
    key_type: string;
    rate_limit_per_minute?: number;
    rate_limit_per_hour?: number;
    rate_limit_per_day?: number;
    expires_at?: string;
  }): Promise<{ api_key: string } & APIKey> {
    const response = await api.post(`/enterprise/organizations/${orgSlug}/api-keys`, data);
    return response.data;
  }

  static async updateAPIKey(orgSlug: string, keyId: number, data: Partial<APIKey>): Promise<APIKey> {
    const response = await api.put(`/enterprise/organizations/${orgSlug}/api-keys/${keyId}`, data);
    return response.data;
  }

  static async deleteAPIKey(orgSlug: string, keyId: number): Promise<void> {
    await api.delete(`/enterprise/organizations/${orgSlug}/api-keys/${keyId}`);
  }

  // Usage Analytics
  static async getUsageAnalytics(orgSlug: string): Promise<UsageAnalytics> {
    const response = await api.get(`/enterprise/organizations/${orgSlug}/analytics`);
    return response.data;
  }

  // Billing Management
  static async getBillingInfo(): Promise<any> {
    const response = await api.get('/enterprise/billing');
    return response.data;
  }

  static async getSubscriptionPlans(): Promise<any[]> {
    const response = await api.get('/enterprise/subscription-plans');
    return response.data;
  }

  static async changeSubscription(data: { tier: string; billing_cycle: string }): Promise<any> {
    const response = await api.post('/enterprise/subscription/change', data);
    return response.data;
  }

  static async getInvoices(): Promise<any[]> {
    const response = await api.get('/enterprise/invoices');
    return response.data;
  }

  static async downloadInvoice(invoiceId: number): Promise<Blob> {
    const response = await api.get(`/enterprise/invoices/${invoiceId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  }

  static async getPaymentMethods(): Promise<any[]> {
    const response = await api.get('/enterprise/payment-methods');
    return response.data;
  }

  // Security & Compliance
  static async getAuditLogs(params?: { 
    range?: string; 
    action?: string; 
    user?: string; 
  }): Promise<any[]> {
    const response = await api.get('/enterprise/audit-logs', { params });
    return response.data;
  }

  static async getSecuritySettings(): Promise<any> {
    const response = await api.get('/enterprise/security-settings');
    return response.data;
  }

  static async updateSecuritySettings(data: any): Promise<any> {
    const response = await api.put('/enterprise/security-settings', data);
    return response.data;
  }

  static async getComplianceReports(): Promise<any[]> {
    const response = await api.get('/enterprise/compliance-reports');
    return response.data;
  }

  static async generateComplianceReport(data: {
    report_type: string;
    period_start: string;
    period_end: string;
  }): Promise<any> {
    const response = await api.post('/enterprise/compliance-reports', data);
    return response.data;
  }

  static async downloadComplianceReport(reportId: number): Promise<Blob> {
    const response = await api.get(`/enterprise/compliance-reports/${reportId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  }
}

export default EnterpriseAPIService;
