try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: web3 package not available. Some features may be limited.")
    WEB3_AVAILABLE = False
    Web3 = None

import re
import json
import asyncio
from typing import Optional, Dict, Tuple
from app.core.config import settings

try:
    from solcx import compile_source, install_solc, set_solc_version
    SOLCX_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: py-solc-x package not available. Compilation features disabled.")
    SOLCX_AVAILABLE = False

class Web3Service:
    def __init__(self):
        if not WEB3_AVAILABLE:
            print("⚠️  Web3Service initialized without web3 support")
            self.w3 = None
            self.installed_versions = set()
            return
            
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        
        # Track installed Solidity versions
        self.installed_versions = set()
        
    async def _ensure_solc_version(self, version: str) -> bool:
        """Ensure the specified Solidity compiler version is installed"""
        try:
            if version not in self.installed_versions:
                # Install the version if not already installed
                await asyncio.to_thread(install_solc, version)
                self.installed_versions.add(version)
            
            # Set the version to use
            await asyncio.to_thread(set_solc_version, version)
            return True
        except Exception as e:
            print(f"Error installing/setting Solidity version {version}: {e}")
            return False

    async def compile_and_estimate_gas(self, contract_code: str, compiler_version: str = "0.8.20") -> Tuple[bool, Optional[int]]:
        """Compile contract and estimate deployment gas"""
        try:
            # Ensure compiler version is available
            version_ready = await self._ensure_solc_version(compiler_version)
            if not version_ready:
                return False, None
            
            # Compile the contract
            compilation_result = await self._compile_contract(contract_code)
            
            if not compilation_result["success"]:
                return False, None
            
            # Estimate gas for deployment
            bytecode = compilation_result["bytecode"]
            gas_estimate = await self._estimate_deployment_gas_from_bytecode(bytecode)
            
            return True, gas_estimate
            
        except Exception as e:
            print(f"Compilation and gas estimation error: {e}")
            return False, None

    async def _compile_contract(self, contract_code: str) -> Dict:
        """Compile Solidity contract using py-solc-x"""
        try:
            # Run compilation in thread to avoid blocking
            compiled_sol = await asyncio.to_thread(
                compile_source, 
                contract_code,
                output_values=['abi', 'bin', 'bin-runtime']
            )
            
            # Extract contract info (assuming single contract)
            contract_id = list(compiled_sol.keys())[0]
            contract_interface = compiled_sol[contract_id]
            
            return {
                "success": True,
                "bytecode": "0x" + contract_interface['bin'],
                "runtime_bytecode": "0x" + contract_interface['bin-runtime'],
                "abi": contract_interface['abi'],
                "errors": [],
                "warnings": []
            }
            
        except Exception as e:
            return {
                "success": False,
                "bytecode": None,
                "abi": None,
                "errors": [str(e)],
                "warnings": []
            }

    async def _estimate_deployment_gas_from_bytecode(self, bytecode: str) -> Optional[int]:
        """Estimate gas cost for contract deployment from bytecode"""
        try:
            if not bytecode or bytecode == "0x":
                return None
            
            # Base transaction cost
            base_gas = 21000
            
            # Gas cost for deploying bytecode (simplified calculation)
            # Each byte of bytecode costs gas
            bytecode_without_prefix = bytecode[2:] if bytecode.startswith("0x") else bytecode
            bytecode_length = len(bytecode_without_prefix) // 2  # Convert hex to bytes
            
            # Gas cost per byte of bytecode (approximation)
            gas_per_byte = 200
            deployment_gas = bytecode_length * gas_per_byte
            
            total_estimated_gas = base_gas + deployment_gas
            
            # Cap at reasonable limit
            return min(total_estimated_gas, 15000000)
            
        except Exception as e:
            print(f"Gas estimation error: {e}")
            return 100000  # Default fallback

    async def estimate_deployment_gas(self, contract_code: str) -> Optional[int]:
        """Legacy method - estimate gas cost for contract deployment"""
        try:
            # Try to compile and get accurate gas estimate
            success, gas_estimate = await self.compile_and_estimate_gas(contract_code)
            
            if success and gas_estimate:
                return gas_estimate
            
            # Fallback to heuristic-based estimation
            return await self._heuristic_gas_estimation(contract_code)
            
        except Exception as e:
            print(f"Gas estimation error: {e}")
            return 100000  # Default fallback

    async def _heuristic_gas_estimation(self, contract_code: str) -> int:
        """Heuristic-based gas estimation when compilation fails"""
        lines_of_code = len(contract_code.split('\n'))
        functions_count = len(re.findall(r'function\s+\w+', contract_code))
        state_vars = len(re.findall(r'uint|string|bool|address|mapping', contract_code))
        
        # Rough estimation based on code complexity
        base_gas = 21000  # Base transaction cost
        code_complexity_gas = lines_of_code * 200  # Rough estimate per line
        function_gas = functions_count * 2000  # Rough estimate per function
        storage_gas = state_vars * 5000  # Rough estimate per state variable
        
        estimated_gas = base_gas + code_complexity_gas + function_gas + storage_gas
        
        return min(estimated_gas, 15000000)  # Cap at reasonable limit

    async def validate_contract_syntax(self, contract_code: str) -> Dict:
        """Validate contract syntax and detect common issues"""
        errors = []
        warnings = []
        
        # Basic syntax checks
        if 'pragma solidity' not in contract_code:
            errors.append("Missing pragma solidity directive")
        
        if 'contract ' not in contract_code:
            errors.append("No contract definition found")
        
        # Security checks
        if 'transfer(' in contract_code and 'require(' not in contract_code:
            warnings.append("Consider using require() statements for safer transfers")
        
        if '.call{value:' in contract_code:
            warnings.append("Direct call with value detected - ensure proper checks")
        
        if 'tx.origin' in contract_code:
            warnings.append("Using tx.origin can be unsafe - consider using msg.sender")
        
        # Gas optimization warnings
        if 'public' in contract_code and 'external' not in contract_code:
            warnings.append("Consider using 'external' instead of 'public' for functions called externally")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def get_contract_functions(self, contract_code: str) -> list:
        """Extract function signatures from contract code"""
        functions = []
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*(public|external|internal|private)?\s*(view|pure|payable)?\s*(returns\s*\([^)]*\))?\s*\{'
        
        matches = re.finditer(function_pattern, contract_code)
        for match in matches:
            function_name = match.group(1)
            visibility = match.group(2) or 'internal'
            state_mutability = match.group(3) or ''
            returns = match.group(4) or ''
            
            functions.append({
                "name": function_name,
                "visibility": visibility,
                "state_mutability": state_mutability,
                "returns": returns.strip()
            })
        
        return functions
