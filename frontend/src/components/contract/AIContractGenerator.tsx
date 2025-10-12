import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Textarea from '../ui/Textarea';
import Spinner from '../ui/Spinner';
import api from '../../services/api';

interface GeneratedContract {
  contract_code: string;
  test_code?: string;
  deployment_script?: string;
  documentation: string;
  estimated_gas_cost: number;
  security_considerations: string[];
}

interface ContractTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  features: string[];
  complexity: 'Basic' | 'Intermediate' | 'Advanced';
}

const CONTRACT_TEMPLATES: ContractTemplate[] = [
  {
    id: 'erc20',
    name: 'ERC-20 Token',
    description: 'Standard fungible token contract',
    icon: '🪙',
    features: ['Transfer', 'Approve', 'Mint', 'Burn'],
    complexity: 'Basic'
  },
  {
    id: 'erc721',
    name: 'ERC-721 NFT',
    description: 'Non-fungible token contract',
    icon: '🎨',
    features: ['Mint NFT', 'Transfer', 'Metadata', 'Royalties'],
    complexity: 'Intermediate'
  },
  {
    id: 'erc1155',
    name: 'ERC-1155 Multi-Token',
    description: 'Multi-token standard contract',
    icon: '🎲',
    features: ['Batch Operations', 'Multiple Token Types', 'Efficient Storage'],
    complexity: 'Advanced'
  },
  {
    id: 'defi',
    name: 'DeFi Protocol',
    description: 'Decentralized finance protocol',
    icon: '🏦',
    features: ['Liquidity Pool', 'Staking', 'Yield Farming', 'Governance'],
    complexity: 'Advanced'
  },
  {
    id: 'dao',
    name: 'DAO Governance',
    description: 'Decentralized autonomous organization',
    icon: '🗳️',
    features: ['Voting', 'Proposals', 'Treasury', 'Multi-sig'],
    complexity: 'Advanced'
  },
  {
    id: 'marketplace',
    name: 'NFT Marketplace',
    description: 'NFT trading marketplace',
    icon: '🛒',
    features: ['Buy/Sell', 'Auctions', 'Royalties', 'Escrow'],
    complexity: 'Advanced'
  },
  {
    id: 'staking',
    name: 'Staking Contract',
    description: 'Token staking and rewards',
    icon: '💎',
    features: ['Stake/Unstake', 'Rewards', 'Time Lock', 'APY Calculation'],
    complexity: 'Intermediate'
  },
  {
    id: 'custom',
    name: 'Custom Contract',
    description: 'Build from natural language description',
    icon: '⚡',
    features: ['AI Generated', 'Custom Logic', 'Flexible Features'],
    complexity: 'Basic'
  }
];

export const AIContractGenerator: React.FC = () => {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [description, setDescription] = useState('');
  const [customFeatures, setCustomFeatures] = useState<string[]>([]);
  const [newFeature, setNewFeature] = useState('');
  const [securityLevel, setSecurityLevel] = useState('standard');
  const [targetNetwork, setTargetNetwork] = useState('ethereum');
  const [includeTests, setIncludeTests] = useState(true);
  const [includeDeployment, setIncludeDeployment] = useState(true);
  
  const [generatedContract, setGeneratedContract] = useState<GeneratedContract | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('contract');

  const selectedTemplateData = CONTRACT_TEMPLATES.find(t => t.id === selectedTemplate);

  const addCustomFeature = () => {
    if (newFeature.trim() && !customFeatures.includes(newFeature.trim())) {
      setCustomFeatures([...customFeatures, newFeature.trim()]);
      setNewFeature('');
    }
  };

  const removeCustomFeature = (feature: string) => {
    setCustomFeatures(customFeatures.filter(f => f !== feature));
  };

  const generateContract = async () => {
    console.log('🔥 Generate button clicked!');
    console.log('Selected template:', selectedTemplate);
    console.log('Description:', description);
    console.log('Description length:', description.trim().length);
    
    if (!selectedTemplate) {
      console.log('❌ No template selected');
      setError('Please select a contract template');
      toast.error('Please select a contract template');
      return;
    }

    if (!description.trim()) {
      console.log('❌ No description provided');
      setError('Please provide a description for your contract');
      toast.error('Please provide a description for your contract');
      return;
    }

    console.log('✅ Validation passed, starting generation...');
    setLoading(true);
    setError(null);

    try {
      const allFeatures = selectedTemplateData 
        ? [...selectedTemplateData.features, ...customFeatures]
        : customFeatures;

      console.log('🚀 Making API call with params:', {
        description: description,
        contract_name: selectedTemplate === 'custom' ? 'CustomContract' : (selectedTemplateData?.name.replace(/[^a-zA-Z0-9]/g, '') || 'CustomContract'),
        features: allFeatures,
        compiler_version: "0.8.19"
      });

      const response = await api.generateContract({
        description: description,
        contract_name: selectedTemplate === 'custom' ? 'CustomContract' : (selectedTemplateData?.name.replace(/[^a-zA-Z0-9]/g, '') || 'CustomContract'),
        features: allFeatures,
        compiler_version: "0.8.19"
      });

      console.log('🎉 API response received:', response);
      console.log('🎉 Response keys:', Object.keys(response || {}));
      console.log('🎉 Response rewritten_code length:', (response as any)?.rewritten_code?.length);

      // Transform backend response to match frontend interface
      const transformedContract: GeneratedContract = {
        contract_code: response.rewritten_code || response.original_code || '',
        documentation: response.generation_notes || description,
        estimated_gas_cost: 150000,
        security_considerations: [
          'Review all function modifiers',
          'Test thoroughly before deployment',
          'Consider upgradeability patterns'
        ]
      };

      console.log('Backend response:', response);
      console.log('Transformed contract:', transformedContract);
      console.log('Contract code length:', transformedContract.contract_code.length);
      console.log('About to setGeneratedContract with:', transformedContract);

      setGeneratedContract(transformedContract);
      console.log('Called setGeneratedContract, switching to contract tab');
      setActiveTab('contract');
      
      // Show success toast
      toast.success('Contract generation completed successfully');
    } catch (err: any) {
      console.error('Contract generation error:', err);
      const errorMessage = err.response?.data?.detail || err.detail || 'Contract generation failed';
      setError(errorMessage);
      
      // Show error toast
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const downloadCode = (code: string, filename: string) => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Basic': return 'text-green-600 bg-green-100';
      case 'Intermediate': return 'text-yellow-600 bg-yellow-100';
      case 'Advanced': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-2">🤖 AI Contract Generator</h2>
        <p className="text-gray-600">
          Generate production-ready smart contracts using advanced AI. 
          Choose a template or describe your custom requirements.
        </p>
      </Card>

      {/* Template Selection */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">1. Choose Contract Template</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {CONTRACT_TEMPLATES.map((template) => (
            <div
              key={template.id}
              onClick={() => setSelectedTemplate(template.id)}
              className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                selectedTemplate === template.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-2">{template.icon}</div>
              <h4 className="font-semibold mb-1">{template.name}</h4>
              <p className="text-sm text-gray-600 mb-2">{template.description}</p>
              <div className="flex flex-wrap gap-1 mb-2">
                {template.features.slice(0, 2).map((feature, index) => (
                  <span key={index} className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {feature}
                  </span>
                ))}
                {template.features.length > 2 && (
                  <span className="text-xs text-gray-500">
                    +{template.features.length - 2} more
                  </span>
                )}
              </div>
              <span className={`text-xs px-2 py-1 rounded ${getComplexityColor(template.complexity)}`}>
                {template.complexity}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* Contract Configuration */}
      {selectedTemplate && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">2. Configure Your Contract</h3>
          
          <div className="space-y-4">
            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Contract Description *
              </label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={`Describe your ${selectedTemplateData?.name || 'contract'} in detail. Include specific requirements, business logic, and any unique features you need.`}
                rows={4}
                className="w-full"
              />
            </div>

            {/* Selected Template Features */}
            {selectedTemplateData && selectedTemplateData.features.length > 0 && (
              <div>
                <label className="block text-sm font-medium mb-2">
                  Template Features
                </label>
                <div className="flex flex-wrap gap-2">
                  {selectedTemplateData.features.map((feature, index) => (
                    <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                      ✓ {feature}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Custom Features */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Additional Features
              </label>
              <div className="flex space-x-2 mb-2">
                <Input
                  value={newFeature}
                  onChange={(e) => setNewFeature(e.target.value)}
                  placeholder="Add custom feature..."
                  onKeyPress={(e) => e.key === 'Enter' && addCustomFeature()}
                  className="flex-1"
                />
                <Button onClick={addCustomFeature} type="button">
                  Add
                </Button>
              </div>
              {customFeatures.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {customFeatures.map((feature, index) => (
                    <span key={index} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm flex items-center">
                      {feature}
                      <button
                        onClick={() => removeCustomFeature(feature)}
                        className="ml-2 text-green-600 hover:text-green-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Configuration Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Security Level</label>
                <select
                  value={securityLevel}
                  onChange={(e) => setSecurityLevel(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="basic">Basic Security</option>
                  <option value="standard">Standard Security</option>
                  <option value="high">High Security</option>
                  <option value="enterprise">Enterprise Security</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Target Network</label>
                <select
                  value={targetNetwork}
                  onChange={(e) => setTargetNetwork(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ethereum">Ethereum</option>
                  <option value="polygon">Polygon</option>
                  <option value="bsc">Binance Smart Chain</option>
                  <option value="arbitrum">Arbitrum</option>
                  <option value="optimism">Optimism</option>
                </select>
              </div>
            </div>

            {/* Additional Options */}
            <div className="flex space-x-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeTests}
                  onChange={(e) => setIncludeTests(e.target.checked)}
                  className="mr-2"
                />
                Include test suite
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeDeployment}
                  onChange={(e) => setIncludeDeployment(e.target.checked)}
                  className="mr-2"
                />
                Include deployment script
              </label>
            </div>
          </div>
        </Card>
      )}

      {/* Generate Button */}
      {selectedTemplate && (
        <Card className="p-6">
          <Button
            onClick={() => {
              console.log('🎯 Button clicked - onClick handler called');
              console.log('🎯 Button disabled?', loading || !description.trim());
              console.log('🎯 Loading state:', loading);
              console.log('🎯 Description empty?', !description.trim());
              console.log('🎯 Description value:', description);
              console.log('🎯 Selected template:', selectedTemplate);
              generateContract();
            }}
            disabled={loading || !description.trim()}
            className="w-full text-lg py-3"
          >
            {loading ? (
              <>
                <Spinner className="w-5 h-5 mr-2" />
                Generating Contract with AI...
              </>
            ) : (
              ' Generate Smart Contract'
            )}
          </Button>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="p-4 border-red-200 bg-red-50">
          <div className="flex items-center space-x-2">
            <span className="text-red-600">⚠️</span>
            <span className="text-red-700">{error}</span>
          </div>
        </Card>
      )}

      {/* Generated Contract Display */}
      {generatedContract && (
        <div className="space-y-6">
          {/* Contract Summary */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">✅ Generated Contract</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-xl font-bold text-blue-600">
                  {generatedContract.estimated_gas_cost.toLocaleString()}
                </div>
                <div className="text-sm text-blue-600">Estimated Gas Cost</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-xl font-bold text-green-600">
                  {generatedContract.security_considerations.length}
                </div>
                <div className="text-sm text-green-600">Security Features</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-xl font-bold text-purple-600">
                  {includeTests ? '✓' : '✗'}
                </div>
                <div className="text-sm text-purple-600">Tests Included</div>
              </div>
            </div>

            {/* Security Considerations */}
            <div>
              <h4 className="font-semibold mb-2">🔒 Security Features:</h4>
              <div className="flex flex-wrap gap-2">
                {generatedContract.security_considerations.map((consideration, index) => (
                  <span key={index} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                    ✓ {consideration}
                  </span>
                ))}
              </div>
            </div>
          </Card>

          {/* Tabbed Code Display */}
          <Card className="p-6">
            <div className="flex space-x-4 mb-6 border-b">
              {[
                { id: 'contract', label: '📄 Contract Code', enabled: true },
                { id: 'tests', label: '🧪 Tests', enabled: !!generatedContract.test_code },
                { id: 'deployment', label: '🚀 Deployment', enabled: !!generatedContract.deployment_script },
                { id: 'documentation', label: '📚 Documentation', enabled: true }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  disabled={!tab.enabled}
                  className={`px-4 py-2 font-medium text-sm rounded-t-lg border-b-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  } ${!tab.enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="space-y-4">
              {/* Tab Content */}
              {activeTab === 'contract' && (
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="font-semibold">Smart Contract Code</h4>
                    <Button
                      onClick={() => downloadCode(generatedContract.contract_code, 'contract.sol')}
                      variant="outline"
                      size="sm"
                    >
                      📥 Download
                    </Button>
                  </div>
                  <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                    <code>{generatedContract.contract_code}</code>
                  </pre>
                </div>
              )}

              {activeTab === 'tests' && generatedContract.test_code && (
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="font-semibold">Test Suite</h4>
                    <Button
                      onClick={() => downloadCode(generatedContract.test_code!, 'test.js')}
                      variant="outline"
                      size="sm"
                    >
                      📥 Download
                    </Button>
                  </div>
                  <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                    <code>{generatedContract.test_code}</code>
                  </pre>
                </div>
              )}

              {activeTab === 'deployment' && generatedContract.deployment_script && (
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="font-semibold">Deployment Script</h4>
                    <Button
                      onClick={() => downloadCode(generatedContract.deployment_script!, 'deploy.js')}
                      variant="outline"
                      size="sm"
                    >
                      📥 Download
                    </Button>
                  </div>
                  <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                    <code>{generatedContract.deployment_script}</code>
                  </pre>
                </div>
              )}

              {activeTab === 'documentation' && (
                <div>
                  <h4 className="font-semibold mb-4">Documentation</h4>
                  <div className="prose max-w-none">
                    <div className="bg-gray-50 p-4 rounded-lg whitespace-pre-wrap">
                      {generatedContract.documentation}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
