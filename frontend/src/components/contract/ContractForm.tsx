import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Play, Settings, Upload, FileText } from 'lucide-react';
import Button from '../ui/Button';
import Textarea from '../ui/Textarea';
import Input from '../ui/Input';
import Card from '../ui/Card';
import type { ContractForm } from '../../types';

interface ContractFormProps {
  onAnalyze: (data: ContractForm) => void;
  onRewrite: (data: ContractForm) => void;
  isAnalyzing: boolean;
  isRewriting: boolean;
}

const ContractFormComponent: React.FC<ContractFormProps> = ({
  onAnalyze,
  onRewrite,
  isAnalyzing,
  isRewriting
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue
  } = useForm<ContractForm>({
    defaultValues: {
      contract_code: '',
      contract_name: '',
      optimization_level: 'BASIC',
      focus_areas: ['GAS_OPTIMIZATION'],
      preserve_functionality: true,
      target_solidity_version: '0.8.19'
    }
  });
  const contractCode = watch('contract_code');
  const focusAreas = watch('focus_areas');
  
  // Auto-extract contract name when code changes
  React.useEffect(() => {
    if (contractCode && !watch('contract_name')) {
      const match = contractCode.match(/contract\s+(\w+)/);
      if (match) {
        setValue('contract_name', match[1]);
      }
    }
  }, [contractCode, setValue, watch]);

  const handleFocusAreaChange = (area: string, checked: boolean) => {
    const currentAreas = focusAreas || [];
    if (checked) {
      setValue('focus_areas', [...currentAreas, area] as ('GAS_OPTIMIZATION' | 'SECURITY' | 'READABILITY' | 'BEST_PRACTICES')[]);
    } else {
      setValue('focus_areas', currentAreas.filter(a => a !== area) as ('GAS_OPTIMIZATION' | 'SECURITY' | 'READABILITY' | 'BEST_PRACTICES')[]);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setValue('contract_code', content);
      };
      reader.readAsText(file);
    }
  };

  const loadSampleContract = () => {
    const sampleContract = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 private storedData;
    
    event DataStored(uint256 data);
    
    function set(uint256 x) public {
        storedData = x;
        emit DataStored(x);
    }
    
    function get() public view returns (uint256) {
        return storedData;
    }
}`;
    setValue('contract_code', sampleContract);
  };

  return (
    <Card title="Smart Contract Input" className="w-full">
      <form className="space-y-6">
        {/* Contract Code Input */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Contract Code
            </label>
            <div className="flex space-x-2">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={loadSampleContract}
              >
                <FileText className="h-4 w-4 mr-1" />
                Load Sample
              </Button>
              <label className="btn-secondary cursor-pointer text-sm">
                <Upload className="h-4 w-4 mr-1" />
                Upload .sol
                <input
                  type="file"
                  accept=".sol"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </div>
          <Textarea
            {...register('contract_code', { 
              required: 'Contract code is required',
              minLength: { value: 50, message: 'Contract code must be at least 50 characters' }
            })}
            placeholder="Paste your Solidity contract code here..."
            className="font-mono text-sm"
            rows={12}
            error={errors.contract_code?.message}
          />
        </div>        {/* Contract Name */}
        <Input
          {...register('contract_name')}
          label="Contract Name"
          placeholder="Auto-detected from code or enter manually"
          helperText="Will auto-extract from contract code if not provided"
        />

        {/* Optimization Level */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Optimization Level
          </label>
          <div className="grid grid-cols-3 gap-3">
            {['BASIC', 'ADVANCED', 'AGGRESSIVE'].map((level) => (
              <label key={level} className="flex items-center space-x-2 cursor-pointer">
                <input
                  {...register('optimization_level')}
                  type="radio"
                  value={level}
                  className="text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm font-medium">{level}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Focus Areas */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Focus Areas
          </label>
          <div className="grid grid-cols-2 gap-3">
            {[
              { value: 'GAS_OPTIMIZATION', label: 'Gas Optimization' },
              { value: 'SECURITY', label: 'Security' },
              { value: 'READABILITY', label: 'Readability' },
              { value: 'BEST_PRACTICES', label: 'Best Practices' }
            ].map((area) => (
              <label key={area.value} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={focusAreas?.includes(area.value as 'GAS_OPTIMIZATION' | 'SECURITY' | 'READABILITY' | 'BEST_PRACTICES') || false}
                  onChange={(e) => handleFocusAreaChange(area.value, e.target.checked)}
                  className="text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm">{area.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Advanced Options */}
        <div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="mb-3"
          >
            <Settings className="h-4 w-4 mr-1" />
            Advanced Options
          </Button>
          
          {showAdvanced && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-4 border-t pt-4"
            >
              <div className="flex items-center space-x-2">
                <input
                  {...register('preserve_functionality')}
                  type="checkbox"
                  className="text-primary-600 focus:ring-primary-500"
                />
                <label className="text-sm">Preserve Original Functionality</label>
              </div>
              
              <Input
                {...register('target_solidity_version')}
                label="Target Solidity Version"
                placeholder="0.8.19"
                helperText="Target Solidity compiler version for optimization"
              />
            </motion.div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-4 pt-4 border-t">
          <Button
            type="button"
            onClick={handleSubmit(onAnalyze)}
            loading={isAnalyzing}
            disabled={!contractCode || isRewriting}
            className="flex-1"
          >
            <Play className="h-4 w-4 mr-2" />
            Analyze Contract
          </Button>
          
          <Button
            type="button"
            onClick={handleSubmit(onRewrite)}
            loading={isRewriting}
            disabled={!contractCode || isAnalyzing}
            className="flex-1"
            variant="secondary"
          >
            <Settings className="h-4 w-4 mr-2" />
            Rewrite Contract
          </Button>
        </div>
      </form>
    </Card>
  );
};

export default ContractFormComponent;
