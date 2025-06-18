import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Sparkles, FileText, Settings, Plus, Trash2 } from 'lucide-react';
import Button from '../ui/Button';
import Textarea from '../ui/Textarea';
import Input from '../ui/Input';
import Card from '../ui/Card';
import type { ContractGenerationForm } from '../../types';

interface ContractGeneratorProps {
  onGenerate: (data: ContractGenerationForm) => void;
  isGenerating: boolean;
}

const ContractGenerator: React.FC<ContractGeneratorProps> = ({
  onGenerate,
  isGenerating
}) => {
  const [customFeatures, setCustomFeatures] = useState<string[]>(['']);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue
  } = useForm<ContractGenerationForm>({
    defaultValues: {
      description: '',
      contract_name: '',
      features: [],
      contract_type: 'custom',
      target_solidity_version: '0.8.19'
    }
  });

  const contractType = watch('contract_type');
  const description = watch('description');

  // Predefined contract types with suggested features
  const contractTypes = {
    token: {
      name: 'ERC-20 Token',
      description: 'Standard fungible token contract',
      features: ['Mintable', 'Burnable', 'Pausable', 'Ownable', 'Capped Supply']
    },
    nft: {
      name: 'ERC-721 NFT',
      description: 'Non-fungible token contract',
      features: ['Mintable', 'Burnable', 'Enumerable', 'URI Storage', 'Royalties']
    },
    defi: {
      name: 'DeFi Protocol',
      description: 'DeFi-related smart contract',
      features: ['Staking', 'Rewards', 'Liquidity Pool', 'Yield Farming', 'Governance']
    },
    dao: {
      name: 'DAO Governance',
      description: 'Decentralized autonomous organization',
      features: ['Voting', 'Proposals', 'Timelock', 'Treasury', 'Token Gating']
    },
    custom: {
      name: 'Custom Contract',
      description: 'Custom smart contract implementation',
      features: []
    }
  };

  // Auto-generate contract name from description
  React.useEffect(() => {
    if (description && !watch('contract_name')) {
      const words = description.split(' ').filter(word => word.length > 3);
      if (words.length > 0) {
        const contractName = words.slice(0, 2).map(word => 
          word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join('');
        setValue('contract_name', contractName);
      }
    }
  }, [description, setValue, watch]);

  const addCustomFeature = () => {
    setCustomFeatures([...customFeatures, '']);
  };

  const removeCustomFeature = (index: number) => {
    setCustomFeatures(customFeatures.filter((_, i) => i !== index));
  };

  const updateCustomFeature = (index: number, value: string) => {
    const updated = [...customFeatures];
    updated[index] = value;
    setCustomFeatures(updated);
  };

  const handleFormSubmit = (data: ContractGenerationForm) => {
    // Add custom features to the predefined ones
    const selectedFeatures = contractTypes[contractType].features.filter(feature => 
      data.features.includes(feature)
    );
    const validCustomFeatures = customFeatures.filter(feature => feature.trim() !== '');
    
    onGenerate({
      ...data,
      features: [...selectedFeatures, ...validCustomFeatures]
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Card className="p-8">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Generate Smart Contract
            </h2>
            <p className="text-gray-600">
              Describe your contract and let AI generate it for you
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          {/* Contract Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Contract Type
            </label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Object.entries(contractTypes).map(([key, type]) => (
                <label
                  key={key}
                  className={`relative flex flex-col p-3 border rounded-lg cursor-pointer transition-all ${
                    contractType === key
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    {...register('contract_type')}
                    value={key}
                    className="sr-only"
                  />
                  <span className="text-sm font-medium text-gray-900">
                    {type.name}
                  </span>
                  <span className="text-xs text-gray-500 mt-1">
                    {type.description}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Contract Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Contract Description *
            </label>
            <Textarea
              {...register('description', { 
                required: 'Please describe what your contract should do',
                minLength: { value: 20, message: 'Description must be at least 20 characters' }
              })}
              placeholder="Describe what your smart contract should do. Be specific about functionality, features, and requirements. For example: 'A token contract that allows users to stake tokens and earn rewards, with a maximum supply of 1 million tokens and the ability to pause transfers.'"
              rows={4}
              className="w-full"
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">
                {errors.description.message}
              </p>
            )}
          </div>

          {/* Contract Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Contract Name *
            </label>
            <Input
              {...register('contract_name', { 
                required: 'Contract name is required',
                pattern: {
                  value: /^[A-Za-z][A-Za-z0-9_]*$/,
                  message: 'Contract name must start with a letter and contain only letters, numbers, and underscores'
                }
              })}
              placeholder="MyToken"
              className="w-full"
            />
            {errors.contract_name && (
              <p className="text-red-500 text-sm mt-1">
                {errors.contract_name.message}
              </p>
            )}
          </div>

          {/* Features Selection */}
          {contractTypes[contractType].features.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Features to Include
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {contractTypes[contractType].features.map((feature) => (
                  <label
                    key={feature}
                    className="flex items-center space-x-2 p-2 border rounded-lg cursor-pointer hover:bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      {...register('features')}
                      value={feature}
                      className="text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Custom Features */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Custom Features
              </label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addCustomFeature}
                className="flex items-center space-x-1"
              >
                <Plus className="w-4 h-4" />
                <span>Add Feature</span>
              </Button>
            </div>
            {customFeatures.map((feature, index) => (
              <div key={index} className="flex items-center space-x-2 mb-2">
                <Input
                  value={feature}
                  onChange={(e) => updateCustomFeature(index, e.target.value)}
                  placeholder="Enter custom feature"
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => removeCustomFeature(index)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>

          {/* Advanced Options */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-2 text-primary-600 hover:text-primary-700"
            >
              <Settings className="w-4 h-4" />
              <span>Advanced Options</span>
            </button>
            
            {showAdvanced && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ duration: 0.3 }}
                className="mt-4 p-4 bg-gray-50 rounded-lg space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Solidity Version
                  </label>
                  <select
                    {...register('target_solidity_version')}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="0.8.19">0.8.19</option>
                    <option value="0.8.20">0.8.20</option>
                    <option value="0.8.21">0.8.21</option>
                    <option value="0.8.22">0.8.22</option>
                  </select>
                </div>
              </motion.div>
            )}
          </div>

          {/* Generate Button */}
          <div className="flex justify-center pt-4">
            <Button
              type="submit"
              disabled={isGenerating}
              className="flex items-center space-x-2 px-8 py-3"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  <span>Generating Contract...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Generate Smart Contract</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </Card>
    </motion.div>
  );
};

export default ContractGenerator;
