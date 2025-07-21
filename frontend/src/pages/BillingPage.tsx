import React from 'react';
import { BillingDashboard } from '../components/enterprise/BillingDashboard';
import Layout from '../components/layout/Layout';

const BillingPage: React.FC = () => {
  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <BillingDashboard />
      </div>
    </Layout>
  );
};

export default BillingPage;
