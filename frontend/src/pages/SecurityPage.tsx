import React from 'react';
import { SecurityComplianceDashboard } from '../components/enterprise/SecurityComplianceDashboard';
import Layout from '../components/layout/Layout';

const SecurityPage: React.FC = () => {
  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <SecurityComplianceDashboard />
      </div>
    </Layout>
  );
};

export default SecurityPage;
