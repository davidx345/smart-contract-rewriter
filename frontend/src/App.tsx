import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import ContractHistoryPage from './pages/ContractHistoryPage';
import NotFoundPage from './pages/NotFoundPage';
import { useState } from 'react'; // Import useState directly, React import removed
import type { ContractOutput } from './types'; // Import ContractOutput type

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  // Lifted state
  const [contractOutput, setContractOutput] = useState<ContractOutput | null>(null);
  const [activeView, setActiveView] = useState<'form' | 'analysis' | 'rewrite'>('form');

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route 
                index 
                element={
                  <HomePage 
                    contractOutput={contractOutput}
                    setContractOutput={setContractOutput}
                    activeView={activeView}
                    setActiveView={setActiveView}
                  />
                } 
              />
              <Route path="history" element={<ContractHistoryPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
          
          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#fff',
                color: '#374151',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
              },
              success: {
                iconTheme: {
                  primary: '#10B981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#EF4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
