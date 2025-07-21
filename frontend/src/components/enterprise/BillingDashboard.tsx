import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import api from '../../services/api';

interface SubscriptionPlan {
  tier: string;
  name: string;
  price_monthly: number;
  price_yearly: number;
  monthly_contract_limit: number;
  monthly_ai_analysis_limit: number;
  monthly_api_calls_limit: number;
  storage_limit_mb: number;
  custom_branding: boolean;
  sso_enabled: boolean;
  audit_logging: boolean;
  priority_support: boolean;
  features: string[];
}

interface BillingInfo {
  subscription_tier: string;
  billing_cycle: 'monthly' | 'yearly';
  current_period_start: string;
  current_period_end: string;
  next_billing_date: string;
  amount_due: number;
  payment_status: string;
  usage_overage: number;
}

interface Invoice {
  id: number;
  invoice_number: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  issue_date: string;
  due_date: string;
  download_url?: string;
}

interface PaymentMethod {
  id: number;
  type: 'card' | 'bank';
  last_four: string;
  brand?: string;
  expires_at?: string;
  is_default: boolean;
}

export const BillingDashboard: React.FC = () => {
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for plan changes
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [updating, setUpdating] = useState(false);

  // State for payment method
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [addingPayment, setAddingPayment] = useState(false);

  useEffect(() => {
    loadBillingData();
  }, []);

  const loadBillingData = async () => {
    try {
      const [billingResponse, plansResponse, invoicesResponse, paymentResponse] = await Promise.all([
        api.get('/enterprise/billing'),
        api.get('/enterprise/subscription-plans'),
        api.get('/enterprise/invoices'),
        api.get('/enterprise/payment-methods')
      ]);

      setBilling(billingResponse.data);
      setPlans(plansResponse.data);
      setInvoices(invoicesResponse.data);
      setPaymentMethods(paymentResponse.data);
      setLoading(false);
    } catch (err: any) {
      setError('Failed to load billing data');
      setLoading(false);
    }
  };

  const changePlan = async () => {
    if (!selectedPlan) return;

    setUpdating(true);
    try {
      await api.post('/enterprise/subscription/change', {
        tier: selectedPlan.tier,
        billing_cycle: billingCycle
      });

      await loadBillingData();
      setShowPlanModal(false);
      setSelectedPlan(null);
    } catch (err: any) {
      setError('Failed to change subscription plan');
    } finally {
      setUpdating(false);
    }
  };

  const downloadInvoice = async (invoiceId: number) => {
    try {
      const response = await api.get(`/enterprise/invoices/${invoiceId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${invoiceId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download invoice');
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'free': return 'text-gray-600 bg-gray-100 border-gray-200';
      case 'starter': return 'text-blue-600 bg-blue-100 border-blue-200';
      case 'professional': return 'text-purple-600 bg-purple-100 border-purple-200';
      case 'enterprise': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'text-green-600 bg-green-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
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
          <h1 className="text-2xl font-bold text-gray-900">Billing & Subscription</h1>
          <p className="text-gray-600">Manage your subscription, billing, and payment methods</p>
        </div>
        <Button onClick={() => setShowPlanModal(true)}>
          Change Plan
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

      {/* Current Subscription */}
      {billing && (
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Current Subscription</h3>
              <div className="mt-2 flex items-center space-x-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTierColor(billing.subscription_tier)}`}>
                  {billing.subscription_tier.toUpperCase()}
                </span>
                <span className="text-gray-600">
                  {billing.billing_cycle === 'yearly' ? 'Annual' : 'Monthly'} billing
                </span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(billing.payment_status)}`}>
                  {billing.payment_status}
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">
                {formatPrice(billing.amount_due)}
              </div>
              <div className="text-sm text-gray-600">
                Next billing: {new Date(billing.next_billing_date).toLocaleDateString()}
              </div>
              {billing.usage_overage > 0 && (
                <div className="text-sm text-orange-600 font-medium">
                  Overage: {formatPrice(billing.usage_overage)}
                </div>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Available Plans */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Available Plans</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map(plan => (
            <div
              key={plan.tier}
              className={`p-0 cursor-pointer transition-all duration-200 hover:shadow-lg ${
                billing?.subscription_tier === plan.tier 
                  ? `border-2 ${getTierColor(plan.tier)}`
                  : 'border border-gray-200'
              } rounded-lg`}
              onClick={() => {
                setSelectedPlan(plan);
                setShowPlanModal(true);
              }}
              tabIndex={0}
              role="button"
              onKeyPress={e => {
                if (e.key === 'Enter' || e.key === ' ') {
                  setSelectedPlan(plan);
                  setShowPlanModal(true);
                }
              }}
            >
              <Card className="p-6 h-full">
                <div className="text-center">
                  <h4 className="text-lg font-semibold">{plan.name}</h4>
                <div className="mt-2">
                  <span className="text-3xl font-bold">
                    {plan.price_monthly === 0 ? 'Free' : formatPrice(plan.price_monthly)}
                  </span>
                  {plan.price_monthly > 0 && (
                    <span className="text-gray-600">/month</span>
                  )}
                </div>
                {plan.price_yearly > 0 && (
                  <div className="text-sm text-gray-600">
                    {formatPrice(plan.price_yearly)}/year (save 20%)
                  </div>
                )}
                </div>

                <div className="mt-6 space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Contract analyses</span>
                  <span className="font-medium">
                    {plan.monthly_contract_limit === -1 ? 'Unlimited' : plan.monthly_contract_limit}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>AI analyses</span>
                  <span className="font-medium">
                    {plan.monthly_ai_analysis_limit === -1 ? 'Unlimited' : plan.monthly_ai_analysis_limit}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>API calls</span>
                  <span className="font-medium">
                    {plan.monthly_api_calls_limit === -1 ? 'Unlimited' : plan.monthly_api_calls_limit}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Storage</span>
                  <span className="font-medium">
                    {plan.storage_limit_mb === -1 ? 'Unlimited' : `${plan.storage_limit_mb} MB`}
                  </span>
                </div>
              </div>

              {plan.features.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <ul className="space-y-1">
                    {plan.features.slice(0, 3).map((feature, index) => (
                      <li key={index} className="text-sm text-gray-600 flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        {feature}
                      </li>
                    ))}
                    {plan.features.length > 3 && (
                      <li className="text-sm text-gray-500">
                        +{plan.features.length - 3} more features
                      </li>
                    )}
                  </ul>
                </div>
              )}

              {billing?.subscription_tier === plan.tier && (
                <div className="mt-4 py-2 text-center text-sm font-medium text-blue-600">
                  Current Plan
                </div>
              )}
              </Card>
            </div>
          ))}
        </div>
      </div>

      {/* Payment Methods */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Payment Methods</h3>
          <Button onClick={() => setShowPaymentModal(true)}>
            + Add Payment Method
          </Button>
        </div>

        <Card className="overflow-hidden">
          {paymentMethods.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No payment methods added yet
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {paymentMethods.map(method => (
                <div key={method.id} className="p-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-8 h-8 bg-gray-100 rounded flex items-center justify-center">
                      {method.type === 'card' ? '💳' : '🏦'}
                    </div>
                    <div>
                      <div className="font-medium">
                        {method.brand} ending in {method.last_four}
                      </div>
                      {method.expires_at && (
                        <div className="text-sm text-gray-600">
                          Expires {new Date(method.expires_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                    {method.is_default && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-600 rounded">
                        Default
                      </span>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    {!method.is_default && (
                      <button className="text-blue-600 hover:text-blue-800 text-sm">
                        Make Default
                      </button>
                    )}
                    <button className="text-red-600 hover:text-red-800 text-sm">
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Billing History */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Billing History</h3>
        <Card className="overflow-hidden">
          {invoices.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No invoices yet
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Invoice
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {invoices.map(invoice => (
                    <tr key={invoice.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        #{invoice.invoice_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                        {formatPrice(invoice.amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(invoice.status)}`}>
                          {invoice.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(invoice.issue_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button
                          onClick={() => downloadInvoice(invoice.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Download
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      {/* Plan Change Modal */}
      {showPlanModal && selectedPlan && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">
              Change to {selectedPlan.name}
            </h3>
            
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">Monthly billing</span>
                  <span className="text-lg font-bold">
                    {formatPrice(selectedPlan.price_monthly)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-medium">Yearly billing</span>
                  <div className="text-right">
                    <span className="text-lg font-bold">
                      {formatPrice(selectedPlan.price_yearly)}
                    </span>
                    <div className="text-sm text-green-600">Save 20%</div>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium">Billing Cycle</label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="monthly"
                      checked={billingCycle === 'monthly'}
                      onChange={(e) => setBillingCycle(e.target.value as 'monthly' | 'yearly')}
                      className="mr-2"
                    />
                    Monthly
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="yearly"
                      checked={billingCycle === 'yearly'}
                      onChange={(e) => setBillingCycle(e.target.value as 'monthly' | 'yearly')}
                      className="mr-2"
                    />
                    Yearly
                  </label>
                </div>
              </div>

              <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                Changes will take effect at the start of your next billing cycle.
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={changePlan}
                  disabled={updating}
                  className="flex-1"
                >
                  {updating ? 'Updating...' : 'Confirm Change'}
                </Button>
                <Button
                  onClick={() => {
                    setShowPlanModal(false);
                    setSelectedPlan(null);
                  }}
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

      {/* Add Payment Method Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Add Payment Method</h3>
            <div className="space-y-4">
              <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg text-center">
                <div className="text-gray-500 mb-2">💳</div>
                <p className="text-sm text-gray-600">
                  Stripe payment integration would be implemented here
                </p>
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={() => setShowPaymentModal(false)}
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
