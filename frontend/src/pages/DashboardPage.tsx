import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

interface UserStats {
  total_contracts_analyzed: number;
  total_contracts_generated: number;
  total_api_calls: number;
  monthly_api_calls: number;
  contracts_this_week: number;
  average_analysis_time: number;
  most_used_features: string[];
  registration_date: string;
  last_activity?: string;
}

export const DashboardPage = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUserStats();
  }, []);

  const fetchUserStats = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/auth/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch user stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getRoleDisplayName = (role: string) => {
    const roleMap: Record<string, string> = {
      user: 'Basic User',
      premium: 'Premium User',
      enterprise: 'Enterprise User',
      admin: 'Administrator',
    };
    return roleMap[role] || role;
  };

  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      active: 'text-green-600 bg-green-100',
      pending: 'text-yellow-600 bg-yellow-100',
      suspended: 'text-red-600 bg-red-100',
      inactive: 'text-gray-600 bg-gray-100',
    };
    return colorMap[status] || 'text-gray-600 bg-gray-100';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-64 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="h-64 bg-gray-200 rounded-lg lg:col-span-2"></div>
              <div className="h-64 bg-gray-200 rounded-lg"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Welcome back, {user?.full_name}!
              </h1>
              <p className="text-gray-600 mt-1">
                Here's your SoliVolt activity overview
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(user?.status || 'inactive')}`}>
                {user?.status?.charAt(0).toUpperCase()}{user?.status?.slice(1)}
              </span>
              <Button variant="outline" onClick={logout}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Contracts Analyzed</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.total_contracts_analyzed || user?.contracts_analyzed || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Contracts Generated</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.total_contracts_generated || user?.contracts_generated || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">API Calls This Month</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.monthly_api_calls || user?.api_calls_this_month || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg. Analysis Time</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.average_analysis_time ? `${stats.average_analysis_time.toFixed(1)}s` : '2.5s'}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <Card className="p-6 lg:col-span-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button 
                className="h-24 flex flex-col items-center justify-center text-center"
                onClick={() => {
                  // Navigate to contract analysis
                  window.location.href = '/#analyze';
                }}
              >
                <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Analyze Contract
              </Button>

              <Button 
                variant="outline"
                className="h-24 flex flex-col items-center justify-center text-center"
                onClick={() => {
                  // Navigate to contract generation
                  window.location.href = '/#generate';
                }}
              >
                <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                </svg>
                Generate Contract
              </Button>

              <Button 
                variant="outline"
                className="h-24 flex flex-col items-center justify-center text-center"
                onClick={() => {
                  // Navigate to contract history
                  window.location.href = '/history';
                }}
              >
                <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                View History
              </Button>

              <Button 
                variant="outline"
                className="h-24 flex flex-col items-center justify-center text-center"
                onClick={() => {
                  // Navigate to profile
                  window.location.href = '/profile';
                }}
              >
                <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Edit Profile
              </Button>
            </div>
          </Card>

          {/* User Profile Summary */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Summary</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-600">Role</p>
                <p className="text-sm text-gray-900">{getRoleDisplayName(user?.role || 'user')}</p>
              </div>
              
              <div>
                <p className="text-sm font-medium text-gray-600">Email</p>
                <p className="text-sm text-gray-900">{user?.email}</p>
                {!user?.email_verified && (
                  <p className="text-xs text-red-600 mt-1">Email not verified</p>
                )}
              </div>

              {user?.company && (
                <div>
                  <p className="text-sm font-medium text-gray-600">Company</p>
                  <p className="text-sm text-gray-900">{user.company}</p>
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-gray-600">Member Since</p>
                <p className="text-sm text-gray-900">
                  {formatDate(stats?.registration_date || user?.created_at || '')}
                </p>
              </div>

              {user?.last_login && (
                <div>
                  <p className="text-sm font-medium text-gray-600">Last Login</p>
                  <p className="text-sm text-gray-900">
                    {formatDate(user.last_login)}
                  </p>
                </div>
              )}

              {stats?.most_used_features && stats.most_used_features.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-600">Most Used Features</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {stats.most_used_features.map((feature, index) => (
                      <span 
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                      >
                        {feature.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Getting Started Guide for New Users */}
        {(user?.contracts_analyzed === 0 && user?.contracts_generated === 0) && (
          <Card className="p-6 mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <div className="flex items-start">
              <div className="p-2 bg-blue-100 rounded-lg mr-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Welcome to SoliVolt! 🚀
                </h3>
                <p className="text-gray-600 mb-4">
                  Get started by analyzing your first smart contract or generating a new one. 
                  Our AI-powered platform will help you build secure, optimized contracts.
                </p>
                <div className="flex space-x-3">
                  <Button onClick={() => window.location.href = '/#analyze'}>
                    Analyze a Contract
                  </Button>
                  <Button variant="outline" onClick={() => window.location.href = '/#generate'}>
                    Generate Contract
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};
