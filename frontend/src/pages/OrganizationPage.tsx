import React from 'react';
import { OrganizationDashboard } from '../components/enterprise/OrganizationDashboard';
import Layout from '../components/layout/Layout';

const OrganizationPage: React.FC = () => {
  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <OrganizationDashboard />
      </div>
    </Layout>
  );
};

export default OrganizationPage;
