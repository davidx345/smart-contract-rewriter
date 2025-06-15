import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import ContractFormComponent from '../components/contract/ContractForm';
import AnalysisDisplay from '../components/contract/AnalysisDisplay';
import RewriteDisplay from '../components/contract/RewriteDisplay';
import Spinner from '../components/ui/Spinner';
import { apiService } from '../services/api';
import type { ContractForm, ContractOutput, APIError, ValidationError } from '../types';

const HomePage: React.FC = () => {
  const [contractOutput, setContractOutput] = useState<ContractOutput | null>(null);
  const [loadingAction, setLoadingAction] = useState<'analyze' | 'rewrite' | null>(null); // New state
  const [error, setError] = useState<string | null>(null); // UI error state
  const [activeView, setActiveView] = useState<'form' | 'analysis' | 'rewrite'>('form');

  const handleAnalyze = async (formData: ContractForm) => {
    setLoadingAction('analyze'); // Set specific loading action
    setError(null); // Clear UI error
    setContractOutput(null); // Clear previous output
    try {
      const extractContractName = (code: string): string => {
        const match = code.match(/contract\\s+(\\w+)/);
        return match ? match[1] : "UntitledContract";
      };

      const contractInput = {
        source_code: formData.contract_code,
        contract_name: formData.contract_name?.trim() || extractContractName(formData.contract_code),
        compiler_version: formData.target_solidity_version || "0.8.19"
      };
      const result: ContractOutput = await apiService.analyzeContract(contractInput);
      setContractOutput(result);
      if (result.analysis_report) {
        setActiveView('analysis');
        toast.success(result.message || 'Contract analysis completed!');
      } else {
        setError(result.message || 'Analysis did not produce a report.');
        toast.error(result.message || 'Analysis did not produce a report.');
      }
    } catch (err: unknown) {
      const apiError = err as APIError;
      console.error('Analysis failed:', err);
      setContractOutput(null);
      let errorMessage = 'Failed to analyze contract';
      if (apiError.detail) {
        if (Array.isArray(apiError.detail)) {
          errorMessage = apiError.detail.map((validationErr: ValidationError) => validationErr.msg || String(validationErr)).join(', ');
        } else {
          errorMessage = apiError.detail;
        }
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoadingAction(null); // Clear loading action
    }/analyze RAW BODY: b'{"source_code":"// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.0;\\n\\ncontract SimpleStorage {\\n    uint256 private storedData;\\n    \\n    event DataStored(uint256 data);\\n    \\n    function set(uint256 x) public {\\n        storedData = x;\\n        emit DataStored(x);\\n    }\\n    \\n    function get() public view returns (uint256) {\\n        return storedData;\\n    }\\n}","contract_name":"SimpleStorage","compiler_version":"0.8.19"}'
/opt/render/project/src/.venv/lib/python3.11/site-packages/solcx/install.py:714: UnexpectedVersionWarning: Installed solc version is v0.8.19+commit.7dd6d404, expecting v0.8.19
  warnings.warn(
INFO:     102.89.68.162:0 - "POST /api/v1/contracts/analyze HTTP/1.1" 200 OK
DB Error logging analysis for SimpleStorage: (builtins.TypeError) Object of type GasFunctionAnalysis is not JSON serializable
[SQL: INSERT INTO contract_analyses (user_id, contract_name, original_code, analysis_report, vulnerabilities_found, gas_analysis, requested_at, completed_at) VALUES (%(user_id)s, %(contract_name)s, %(original_code)s, %(analysis_report)s, %(vulnerabilities_found)s, %(gas_analysis)s, %(requested_at)s, %(completed_at)s) RETURNING contract_analyses.id]
[parameters: [{'completed_at': datetime.datetime(2025, 6, 15, 11, 59, 33, 220474, tzinfo=datetime.timezone.utc), 'gas_analysis': [GasFunctionAnalysis(function_name= ... (1985 characters truncated) ... _original': 105600, 'estimated_total_gas_optimized': None, 'total_gas_savings_absolute': None, 'total_gas_savings_percentage': None}, 'user_id': None}]]
INFO:     102.89.68.162:0 - "GET /api/v1/contracts/history?skip=0&limit=10 HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 922, in do_execute
    cursor.execute(statement, parameters)
psycopg2.errors.UndefinedTable: relation "contract_analyses" does not exist
LINE 2: FROM contract_analyses ORDER BY contract_analyses.requested_...
             ^
The above exception was the direct cause of the following exception:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/protocols/http/h11_impl.py", line 408, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/fastapi/applications.py", line 1106, in __call__
    await super().__call__(scope, receive, send)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/applications.py", line 122, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/middleware/errors.py", line 184, in __call__
    raise exc
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/prometheus_fastapi_instrumentator/middleware.py", line 169, in __call__
    raise exc
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/prometheus_fastapi_instrumentator/middleware.py", line 167, in __call__
    await self.app(scope, receive, send_wrapper)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/backend/app/apis/v1/endpoints/contracts.py", line 115, in get_contract_history
    analyses_db = db.query(ContractAnalysisDB).order_by(ContractAnalysisDB.requested_at.desc()).offset(skip).limit(limit).all()
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2693, in all
    return self._iter().all()  # type: ignore
           ^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2847, in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
                                                  ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2308, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2190, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/orm/context.py", line 293, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1416, in execute
    return meth(
           ^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 516, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1639, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2343, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/opt/render/project/src/.venv/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 922, in do_execute
    cursor.execute(statement, parameters)
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "contract_analyses" does not exist
LINE 2: FROM contract_analyses ORDER BY contract_analyses.requested_...
             ^
[SQL: SELECT contract_analyses.id AS contract_analyses_id, contract_analyses.user_id AS contract_analyses_user_id, contract_analyses.contract_name AS contract_analyses_contract_name, contract_analyses.original_code AS contract_analyses_original_code, contract_analyses.analysis_report AS contract_analyses_analysis_report, contract_analyses.vulnerabilities_found AS contract_analyses_vulnerabilities_found, contract_analyses.gas_analysis AS contract_analyses_gas_analysis, contract_analyses.requested_at AS contract_analyses_requested_at, contract_analyses.completed_at AS contract_analyses_completed_at 
FROM contract_analyses ORDER BY contract_analyses.requested_at DESC 
 LIMIT %(param_1)s OFFSET %(param_2)s]
[parameters: {'param_1': 10, 'param_2': 0}]
(Background on this error at: https://sqlalche.me/e/20/f405)
/analyze RAW BODY: b'{"source_code":"// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.0;\\n\\ncontract SimpleStorage {\\n    uint256 private storedData;\\n    \\n    event DataStored(uint256 data);\\n    \\n    function set(uint256 x) public {\\n        storedData = x;\\n        emit DataStored(x);\\n    }\\n    \\n    function get() public view returns (uint256) {\\n        return storedData;\\n    }\\n}","contract_name":"SimpleStorage","compiler_version":"0.8.19"}'
INFO:     102.89.68.162:0 - "POST /api/v1/contracts/analyze HTTP/1.1" 200 OK
DB Error logging analysis for SimpleStorage: (builtins.TypeError) Object of type GasFunctionAnalysis is not JSON serializable
[SQL: INSERT INTO contract_analyses (user_id, contract_name, original_code, analysis_report, vulnerabilities_found, gas_analysis, requested_at, completed_at) VALUES (%(user_id)s, %(contract_name)s, %(original_code)s, %(analysis_report)s, %(vulnerabilities_found)s, %(gas_analysis)s, %(requested_at)s, %(completed_at)s) RETURNING contract_analyses.id]
[parameters: [{'completed_at': datetime.datetime(2025, 6, 15, 12, 1, 56, 637167, tzinfo=datetime.timezone.utc), 'gas_analysis': [GasFunctionAnalysis(function_name=' ... (1701 characters truncated) ... _original': 105600, 'estimated_total_gas_optimized': None, 'total_gas_savings_absolute': None, 'total_gas_savings_percentage': None}, 'user_id': None}]]
     ==> Detected service running on port 10000
     ==> Docs on specifying a port: https://render.com/docs/web-services#port-binding
/analyze RAW BODY: b'{"source_code":"// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.0;\\n\\ncontract SimpleStorage {\\n    uint256 private storedData;\\n    \\n    event DataStored(uint256 data);\\n    \\n    function set(uint256 x) public {\\n        storedData = x;\\n        emit DataStored(x);\\n    }\\n    \\n    function get() public view returns (uint256) {\\n        return storedData;\\n    }\\n}","contract_name":"SimpleStorage","compiler_version":"0.8.19"}'
INFO:     102.89.68.162:0 - "POST /api/v1/contracts/analyze HTTP/1.1" 200 OK
DB Error logging analysis for SimpleStorage: (builtins.TypeError) Object of type GasFunctionAnalysis is not JSON serializable
[SQL: INSERT INTO contract_analyses (user_id, contract_name, original_code, analysis_report, vulnerabilities_found, gas_analysis, requested_at, completed_at) VALUES (%(user_id)s, %(contract_name)s, %(original_code)s, %(analysis_report)s, %(vulnerabilities_found)s, %(gas_analysis)s, %(requested_at)s, %(completed_at)s) RETURNING contract_analyses.id]
[parameters: [{'completed_at': datetime.datetime(2025, 6, 15, 12, 3, 20, 843885, tzinfo=datetime.timezone.utc), 'gas_analysis': [GasFunctionAnalysis(function_name=' ... (1828 characters truncated) ... _original': 105600, 'estimated_total_gas_optimized': None, 'total_gas_savings_absolute': None, 'total_gas_savings_percentage': None}, 'user_id': None}]]
  };

  const handleRewrite = async (formData: ContractForm) => {
    if (!formData.contract_code) {
      setError("Please enter some contract code.");
      return;
    }
    setLoadingAction('rewrite'); // Set specific loading action
    setError(null); // Clear UI error
    // Preserve analysis report if it exists, clear rewrite specific parts
    setContractOutput(prev => prev ? { ...prev, rewrite_report: undefined, rewritten_code: undefined, message: 'Processing rewrite...' } : null);
    try {
      const extractContractName = (code: string): string => {
        const match = code.match(/contract\\s+(\\w+)/);
        return match ? match[1] : "UntitledContract";
      };

      const optimizationGoalsMap = {
        'GAS_OPTIMIZATION': 'gas_efficiency',
        'SECURITY': 'security_hardening',
        'READABILITY': 'readability',
        'BEST_PRACTICES': 'modularity'
      } as const;

      const optimization_goals = formData.focus_areas.map(area =>
        optimizationGoalsMap[area as keyof typeof optimizationGoalsMap] || 'gas_efficiency'
      );

      const optimizationRequest = {
        source_code: formData.contract_code,
        contract_name: formData.contract_name?.trim() || extractContractName(formData.contract_code),
        compiler_version: formData.target_solidity_version || "0.8.19",
        optimization_goals,
        preserve_functionality: formData.preserve_functionality
      };
      const result: ContractOutput = await apiService.rewriteContract(optimizationRequest);
      // Update contractOutput with the new rewrite result, keeping existing analysis if any
      setContractOutput(prev => ({
        ...(prev || { original_code: formData.contract_code, request_id: '', processing_time_seconds: 0, message: '' }), // Ensure base structure if prev is null
        ...result // Spread the new result, overwriting relevant fields
      }));
      if (result.rewritten_code && result.rewrite_report) {
        setActiveView('rewrite');
        toast.success(result.message || 'Contract rewrite completed!');
      } else {
        setError(result.message || 'Rewrite did not produce the expected output.');
        toast.error(result.message || 'Rewrite did not produce the expected output.');
      }
    } catch (err: unknown) {
      const apiError = err as APIError;
      console.error('Rewrite failed:', err);
      let errorMessage = 'Failed to rewrite contract';
      if (apiError.detail) {
        if (Array.isArray(apiError.detail)) {
          errorMessage = apiError.detail.map((validationErr: ValidationError) => validationErr.msg || String(validationErr)).join(', ');
        } else {
          errorMessage = apiError.detail;
        }
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      // When rewrite fails, we might want to clear only rewrite-specific parts or keep existing state
      setContractOutput(prev => prev ? 
        { ...prev, rewrite_report: undefined, rewritten_code: undefined, message: errorMessage } : 
        { request_id: "", original_code: formData.contract_code, processing_time_seconds:0, message: errorMessage });
      toast.error(errorMessage);
    } finally {
      setLoadingAction(null); // Clear loading action
    }
  };

  const resetView = () => {
    setActiveView('form');
    setContractOutput(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="gradient-bg text-white">
        <div className="container mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Smart Contract Rewriter
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100">
              AI-powered optimization for your Solidity contracts
            </p>
            <div className="flex flex-wrap justify-center gap-6 text-sm md:text-base">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>Gas Optimization</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span>Security Analysis</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                <span>Code Quality</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <span>Best Practices</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-12">
        {/* Navigation Breadcrumbs */}
        {activeView !== 'form' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8"
          >
            <nav className="flex items-center space-x-2 text-sm">
              <button 
                onClick={resetView}
                className="text-primary-600 hover:text-primary-800 transition-colors"
              >
                Contract Input
              </button>
              <span className="text-gray-400">/</span>
              <span className="text-gray-600 capitalize">{activeView}</span>
            </nav>
          </motion.div>
        )}

        {/* Content Views */}
        <motion.div
          key={activeView}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {activeView === 'form' && (
            <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-md p-8">
              <h2 className="text-2xl font-bold mb-6 text-center">
                Analyze and Rewrite Your Contract
              </h2>
              <ContractFormComponent 
                onAnalyze={handleAnalyze}
                onRewrite={handleRewrite}
                // Pass specific loading states
                isAnalyzing={loadingAction === 'analyze'}
                isRewriting={loadingAction === 'rewrite'}
              />
            </div>
          )}

          {activeView === 'analysis' && contractOutput?.analysis_report && (
            <div className="max-w-7xl mx-auto">
              <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  Contract Analysis Report
                </h2>
                <p className="text-gray-600">
                  Comprehensive analysis of your smart contract
                </p>
              </div>
              <AnalysisDisplay report={contractOutput.analysis_report} />
            </div>
          )}

          {activeView === 'rewrite' && contractOutput?.rewrite_report && contractOutput?.rewritten_code && contractOutput?.original_code && (
            <div className="max-w-7xl mx-auto">
              <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  Contract Optimization Report
                </h2>
                <p className="text-gray-600">
                  Your optimized smart contract with improvements
                </p>
              </div>
              <RewriteDisplay
                report={contractOutput.rewrite_report}
                originalCode={contractOutput.original_code}
                rewrittenCode={contractOutput.rewritten_code}
                isLoading={loadingAction === 'rewrite'} // Pass specific loading state
                error={error}
              />
            </div>
          )}
        </motion.div>

        {/* Loading States - Now uses loadingAction */}
        {loadingAction && ( // Show spinner if any action is loading
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          >
            <div className="bg-white rounded-lg p-8 max-w-md mx-4">
              <div className="text-center">
                <Spinner size="lg" className="mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {/* Update text based on loadingAction */}
                  {loadingAction === 'analyze' ? 'Analyzing Contract...' : 'Rewriting Contract...'}
                </h3>
                <p className="text-gray-600">
                  {loadingAction === 'analyze' 
                    ? 'AI is analyzing your contract for security issues and optimization opportunities.'
                    : 'AI is rewriting your contract with optimizations and improvements.'
                  }
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  This may take a few moments.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Features Section (shown only on form view) */}
      {activeView === 'form' && (
        <div className="bg-gray-50 py-16">
          <div className="container mx-auto px-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Powered by Advanced AI
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Our AI analyzes your smart contracts and provides comprehensive optimization recommendations
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                {
                  title: 'Gas Optimization',
                  description: 'Reduce transaction costs with intelligent gas usage optimization',
                  icon: '⚡',
                  color: 'bg-yellow-100 text-yellow-600'
                },
                {
                  title: 'Security Analysis',
                  description: 'Identify vulnerabilities and security issues in your code',
                  icon: '🛡️',
                  color: 'bg-green-100 text-green-600'
                },
                {
                  title: 'Code Quality',
                  description: 'Improve readability, maintainability, and best practices',
                  icon: '📝',
                  color: 'bg-blue-100 text-blue-600'
                },
                {
                  title: 'Best Practices',
                  description: 'Apply industry standards and proven patterns',
                  icon: '✨',
                  color: 'bg-purple-100 text-purple-600'
                }
              ].map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 * index }}
                  className="text-center"
                >
                  <div className={`w-16 h-16 ${feature.color} rounded-full flex items-center justify-center text-2xl mx-auto mb-4`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
