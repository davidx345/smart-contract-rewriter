import React from 'react';
import Card from '../ui/Card';
import { XCircle } from 'lucide-react'; 
import { DiffEditor } from '@monaco-editor/react'; // Expect error until npm install
import type { RewriteReport } from '../../types'; 

interface RewriteDisplayProps {
  report: RewriteReport; // Changed from contractOutput to specific report
  originalCode: string;
  rewrittenCode: string;
  isLoading: boolean;
  error: string | null; // Changed from Error | null to string | null
}

// Basic Alert-like component using divs and lucide-react icons
const SimpleAlert: React.FC<{
  variant: 'default' | 'destructive';
  title: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
}> = ({ variant, title, children, icon }) => {
  const baseClasses = "p-4 rounded-md border";
  const variantClasses = {
    default: "bg-blue-50 border-blue-200 text-blue-700",
    destructive: "bg-red-50 border-red-200 text-red-700",
  };
  return (
    <div className={`${baseClasses} ${variantClasses[variant]}`}>
      <div className="flex">
        {icon && <div className="flex-shrink-0 mr-2">{icon}</div>}
        <div className="flex-1">
          {title && <h5 className="font-medium">{title}</h5>}
          <div className="text-sm">{children}</div>
        </div>
      </div>
    </div>
  );
};

const RewriteDisplay: React.FC<RewriteDisplayProps> = ({ report, originalCode, rewrittenCode, isLoading, error }) => {
  if (isLoading) {
    return <p>Loading rewrite information...</p>;
  }

  if (error) {
    return (
      <SimpleAlert variant="destructive" title="Error" icon={<XCircle className="h-4 w-4" />}>
        {/* Display the string error message directly */}
        Failed to load rewrite information: {error}
      </SimpleAlert>
    );
  }

  // Removed !contractOutput check as props are now more specific
  // if (!report || !originalCode || !rewrittenCode) { // Adjusted for new props
  //   return <p>No complete rewrite data available. Please analyze or rewrite a contract first.</p>;
  // }

  // Destructure directly from the report prop
  const {
    suggestions,
    gas_optimization_details,
    security_improvements,
    // Assuming these might come from a more detailed report in future or are part of a base report type
    // compilation_success_original, // These would typically be top-level in ContractOutput
    // compilation_success_rewritten,
    // diff_summary,
    // message
  } = report;

  // const hasRewriteData = rewritten_code || report;

  return (
    <Card title="Contract Rewrite Analysis">
      <div className="space-y-6 p-4">
        {/* Removed message display from here, assuming it's handled by HomePage or part of a general status component */}

        {/* Compilation status and diff summary might be better handled in HomePage or a wrapper component
            as they relate to the overall ContractOutput, not just the RewriteReport part. 
            For now, let's assume they are not part of this component's direct responsibility if not in RewriteReport.
        */}

        {report && (
          <div>
            <h3 className="text-lg font-semibold mb-2">Rewrite Report Details</h3>
            {suggestions && suggestions.length > 0 ? (
              <ul className="list-disc pl-5 space-y-1">
                {suggestions.map((suggestion, index) => (
                  <li key={index} className="text-sm">{suggestion}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No specific rewrite suggestions provided.</p>
            )}
             {gas_optimization_details && (
              <div className="mt-4">
                <h4 className="text-md font-semibold mb-1">Gas Optimization Details:</h4>
                <p className="text-sm">Original Estimated Gas: {gas_optimization_details.original_estimated_gas ?? 'N/A'}</p>
                <p className="text-sm">Optimized Estimated Gas: {gas_optimization_details.optimized_estimated_gas ?? 'N/A'}</p>
                <p className="text-sm">Gas Saved: {gas_optimization_details.gas_saved ?? 'N/A'}</p>
                <p className="text-sm">Gas Savings Percentage: {gas_optimization_details.gas_savings_percentage !== null && gas_optimization_details.gas_savings_percentage !== undefined ? gas_optimization_details.gas_savings_percentage.toFixed(2) + '%' : 'N/A'}</p>
              </div>
            )}
            {security_improvements && security_improvements.length > 0 && (
                <div className="mt-4">
                    <h4 className="text-md font-semibold mb-1">Security Improvements:</h4>
                    <ul className="list-disc pl-5 space-y-1">
                        {security_improvements.map((item, index) => (
                            <li key={index} className="text-sm">{item}</li>
                        ))}
                    </ul>
                </div>
            )}
          </div>
        )}

        {originalCode && rewrittenCode && (
          <div>
            <h3 className="text-lg font-semibold mb-2">Code Comparison</h3>
            <div style={{ height: '400px', border: '1px solid #ccc', borderRadius: '4px' }}>
              <DiffEditor
                height="400px"
                language="solidity"
                original={originalCode}
                modified={rewrittenCode}
                theme="vs-dark"
                options={{
                  readOnly: true,
                  minimap: { enabled: false }
                }}
              />
            </div>
          </div>
        )}

        {/*
        !hasRewriteData && !isLoading && !error && (
          <SimpleAlert variant="default" title="No Rewrite Performed" icon={<AlertTriangle className="h-4 w-4" />}>
            The contract was analyzed, but no rewrite was performed or no rewrite data is available.
          </SimpleAlert>
        )
        */}
      </div>
    </Card>
  );
};

export default RewriteDisplay;
