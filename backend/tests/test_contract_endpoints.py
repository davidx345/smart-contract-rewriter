# filepath: backend/tests/test_contract_endpoints.py
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.models.contract_models import (
    ContractAnalysisRequest, 
    ContractRewriteRequest, 
    OptimizationGoal,
    VulnerabilityType
)

@pytest.mark.asyncio
class TestContractEndpoints:
    
    async def test_analyze_endpoint_success(self, client: AsyncClient):
        """Test successful contract analysis"""
        request_data = {
            "contract_code": """
            pragma solidity ^0.8.0;
            contract SimpleStorage {
                uint256 private storedData;
                function set(uint256 x) public { storedData = x; }
                function get() public view returns (uint256) { return storedData; }
            }
            """,
            "contract_name": "SimpleStorage"
        }
        
        with patch('app.services.contract_processing_service.ContractProcessingService.analyze_contract') as mock_analyze:
            mock_analyze.return_value = {
                "contract_name": "SimpleStorage",
                "vulnerabilities": [
                    {
                        "type": "REENTRANCY",
                        "severity": "HIGH",
                        "description": "Potential reentrancy vulnerability",
                        "line_number": 5,
                        "suggestion": "Use checks-effects-interactions pattern"
                    }
                ],
                "gas_analysis": {
                    "estimated_deployment_cost": 150000,
                    "function_costs": {
                        "set": 25000,
                        "get": 2500
                    }
                },
                "optimization_suggestions": [
                    {
                        "type": "GAS_OPTIMIZATION",
                        "description": "Use uint32 instead of uint256 if values are small",
                        "potential_savings": 5000
                    }
                ],
                "security_score": 7.5,
                "code_quality_metrics": {
                    "complexity": "LOW",
                    "maintainability": "HIGH",
                    "test_coverage": "UNKNOWN"
                }
            }
            
            response = await client.post("/api/v1/contracts/analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["contract_name"] == "SimpleStorage"
            assert len(data["vulnerabilities"]) == 1
            assert data["security_score"] == 7.5
    
    async def test_analyze_endpoint_invalid_contract(self, client: AsyncClient):
        """Test analysis with invalid contract code"""
        request_data = {
            "contract_code": "invalid solidity code",
            "contract_name": "InvalidContract"
        }
        
        with patch('app.services.contract_processing_service.ContractProcessingService.analyze_contract') as mock_analyze:
            mock_analyze.side_effect = Exception("Compilation failed")
            
            response = await client.post("/api/v1/contracts/analyze", json=request_data)
            
            assert response.status_code == 500
            assert "error" in response.json()
    
    async def test_rewrite_endpoint_success(self, client: AsyncClient):
        """Test successful contract rewriting"""
        request_data = {
            "contract_code": """
            pragma solidity ^0.8.0;
            contract SimpleStorage {
                uint256 private storedData;
                function set(uint256 x) public { storedData = x; }
                function get() public view returns (uint256) { return storedData; }
            }
            """,
            "contract_name": "SimpleStorage",
            "optimization_goals": ["GAS_OPTIMIZATION", "SECURITY_ENHANCEMENT"]
        }
        
        with patch('app.services.contract_processing_service.ContractProcessingService.rewrite_contract') as mock_rewrite:
            mock_rewrite.return_value = {
                "original_contract": request_data["contract_code"],
                "rewritten_contract": """
                pragma solidity ^0.8.0;
                contract SimpleStorage {
                    uint32 private storedData;
                    function set(uint32 x) external { storedData = x; }
                    function get() external view returns (uint32) { return storedData; }
                }
                """,
                "changes_made": [
                    {
                        "type": "GAS_OPTIMIZATION",
                        "description": "Changed uint256 to uint32 for gas savings",
                        "line_number": 4
                    }
                ],
                "gas_improvement": {
                    "before": 150000,
                    "after": 140000,
                    "savings": 10000,
                    "percentage_improvement": 6.67
                },
                "security_improvements": [
                    {
                        "vulnerability_fixed": "INTEGER_OVERFLOW",
                        "description": "Added overflow protection"
                    }
                ]
            }
            
            response = await client.post("/api/v1/contracts/rewrite", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "rewritten_contract" in data
            assert "changes_made" in data
            assert data["gas_improvement"]["savings"] == 10000
    
    async def test_rewrite_endpoint_no_optimization_goals(self, client: AsyncClient):
        """Test rewriting without optimization goals"""
        request_data = {
            "contract_code": "pragma solidity ^0.8.0; contract Test {}",
            "contract_name": "Test",
            "optimization_goals": []
        }
        
        response = await client.post("/api/v1/contracts/rewrite", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_history_endpoint(self, client: AsyncClient):
        """Test retrieving contract analysis/rewrite history"""
        with patch('app.apis.v1.endpoints.contracts.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock database query results
            mock_db.query().order_by().limit().offset().all.return_value = []
            
            response = await client.get("/api/v1/contracts/history?limit=10&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            assert "analyses" in data
            assert "rewrites" in data
    
    async def test_analyze_endpoint_validation_error(self, client: AsyncClient):
        """Test analysis endpoint with validation errors"""
        # Missing required fields
        request_data = {
            "contract_code": ""  # Empty contract code
        }
        
        response = await client.post("/api/v1/contracts/analyze", json=request_data)
        
        assert response.status_code == 422
    
    async def test_rewrite_endpoint_invalid_optimization_goal(self, client: AsyncClient):
        """Test rewrite endpoint with invalid optimization goal"""
        request_data = {
            "contract_code": "pragma solidity ^0.8.0; contract Test {}",
            "contract_name": "Test",
            "optimization_goals": ["INVALID_GOAL"]
        }
        
        response = await client.post("/api/v1/contracts/rewrite", json=request_data)
        
        assert response.status_code == 422
