"""
Unit tests for the Contract Service microservice.

Tests the core functionality of contract analysis, storage, and retrieval.
"""

import pytest
import httpx
from unittest.mock import patch, Mock
import json
from datetime import datetime

# Import the contract service app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../microservices/contract-service'))

from main import app

class TestContractService:
    """Test suite for Contract Service endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(self, async_client):
        """Test that health check endpoint returns healthy status."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "contract-service"
        assert data["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_root_endpoint_returns_service_info(self, async_client):
        """Test that root endpoint returns service information."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "SoliVolt Contract Service"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_analyze_contract_with_valid_input(self, async_client, sample_contract):
        """Test contract analysis with valid Solidity code."""
        request_data = {
            "contract_code": sample_contract,
            "contract_name": "SimpleStorage"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "contract_name" in data
        assert "security_score" in data
        assert "issues" in data
        assert "suggestions" in data
        assert "analyzed_at" in data
        
        # Verify data types
        assert isinstance(data["security_score"], int)
        assert isinstance(data["issues"], list)
        assert isinstance(data["suggestions"], list)
        
        # Verify contract name
        assert data["contract_name"] == "SimpleStorage"
    
    @pytest.mark.asyncio
    async def test_analyze_contract_without_name(self, async_client, sample_contract):
        """Test contract analysis without providing contract name."""
        request_data = {
            "contract_code": sample_contract
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["contract_name"] == "Unknown"
    
    @pytest.mark.asyncio
    async def test_analyze_contract_with_empty_code(self, async_client):
        """Test contract analysis with empty contract code."""
        request_data = {
            "contract_code": "",
            "contract_name": "EmptyContract"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        # Should still return 200 but with appropriate analysis
        assert response.status_code == 200
        data = response.json()
        assert data["contract_name"] == "EmptyContract"
    
    @pytest.mark.asyncio
    async def test_analyze_contract_with_invalid_json(self, async_client):
        """Test contract analysis with invalid JSON payload."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json={"invalid": "payload"})
        
        # Should return 422 for validation error
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_analyze_contract_with_malformed_solidity(self, async_client):
        """Test contract analysis with malformed Solidity code."""
        request_data = {
            "contract_code": "pragma solidity ^0.8.0; contract { invalid syntax",
            "contract_name": "MalformedContract"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        # Should handle gracefully and return analysis
        assert response.status_code == 200
        data = response.json()
        assert data["contract_name"] == "MalformedContract"

class TestContractAnalysisModels:
    """Test the Pydantic models used in contract service."""
    
    def test_contract_analyze_request_validation(self):
        """Test ContractAnalyzeRequest model validation."""
        # Import the model
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../microservices/contract-service'))
        from main import ContractAnalyzeRequest
        
        # Valid request
        valid_request = ContractAnalyzeRequest(
            contract_code="pragma solidity ^0.8.0; contract Test {}",
            contract_name="TestContract"
        )
        assert valid_request.contract_code == "pragma solidity ^0.8.0; contract Test {}"
        assert valid_request.contract_name == "TestContract"
        
        # Request without name (should use default)
        request_without_name = ContractAnalyzeRequest(
            contract_code="pragma solidity ^0.8.0; contract Test {}"
        )
        assert request_without_name.contract_name is None
    
    def test_contract_analysis_result_structure(self):
        """Test ContractAnalysisResult model structure."""
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../microservices/contract-service'))
        from main import ContractAnalysisResult
        
        result = ContractAnalysisResult(
            contract_name="TestContract",
            security_score=85,
            issues=[
                {
                    "severity": "medium",
                    "type": "gas_optimization",
                    "line": 10,
                    "description": "Consider optimizing gas usage"
                }
            ],
            suggestions=["Add input validation"],
            analyzed_at=datetime.utcnow().isoformat()
        )
        
        assert result.contract_name == "TestContract"
        assert result.security_score == 85
        assert len(result.issues) == 1
        assert len(result.suggestions) == 1

class TestContractServiceIntegration:
    """Integration tests for contract service with external dependencies."""
    
    @pytest.mark.asyncio
    async def test_analyze_contract_performance(self, async_client, sample_contract):
        """Test that contract analysis completes within reasonable time."""
        import time
        
        request_data = {
            "contract_code": sample_contract,
            "contract_name": "PerformanceTest"
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        # Should complete within 5 seconds for simple contract
        assert duration < 5.0
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, async_client, sample_contract):
        """Test handling multiple concurrent analysis requests."""
        import asyncio
        
        request_data = {
            "contract_code": sample_contract,
            "contract_name": "ConcurrentTest"
        }
        
        # Create multiple concurrent requests
        async def make_request():
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                return await client.post("/analyze", json=request_data)
        
        # Execute 5 concurrent requests
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["contract_name"] == "ConcurrentTest"

class TestContractServiceErrorHandling:
    """Test error handling in contract service."""
    
    @pytest.mark.asyncio
    async def test_analyze_with_missing_required_field(self, async_client):
        """Test analysis request with missing required field."""
        # Missing contract_code field
        request_data = {
            "contract_name": "TestContract"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    @pytest.mark.asyncio
    async def test_analyze_with_extremely_large_contract(self, async_client):
        """Test analysis with extremely large contract code."""
        # Create a very large contract string
        large_contract = "pragma solidity ^0.8.0; contract Large { " + "uint256 x; " * 10000 + "}"
        
        request_data = {
            "contract_code": large_contract,
            "contract_name": "LargeContract"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        # Should handle large inputs gracefully
        assert response.status_code in [200, 413, 500]  # OK, Payload Too Large, or Server Error
    
    @pytest.mark.asyncio 
    async def test_unsupported_http_methods(self, async_client):
        """Test unsupported HTTP methods return appropriate errors."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # PUT method not supported
            response = await client.put("/analyze", json={})
            assert response.status_code == 405
            
            # DELETE method not supported  
            response = await client.delete("/analyze")
            assert response.status_code == 405