"""
Unit tests for the AI Service microservice.

Tests the Google Gemini integration, contract analysis, and generation functionality.
"""

import pytest
import httpx
from unittest.mock import patch, Mock, AsyncMock
import json
from datetime import datetime

# Import the AI service app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../microservices/ai-service'))

from main import app, GeminiService

class TestAIService:
    """Test suite for AI Service endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(self, async_client):
        """Test that health check endpoint returns healthy status."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-service"
        assert data["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_root_endpoint_returns_service_info(self, async_client):
        """Test that root endpoint returns service information."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "SoliVolt AI Service"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    @patch('main.GeminiService.analyze_contract')
    async def test_analyze_contract_with_valid_input(self, mock_analyze, async_client, sample_contract):
        """Test contract analysis with valid Solidity code."""
        # Mock Gemini service response
        mock_analyze.return_value = {
            "security_analysis": {
                "score": 85,
                "vulnerabilities": ["Potential reentrancy in transfer function"],
                "recommendations": ["Add ReentrancyGuard"]
            },
            "gas_analysis": {
                "score": 75,
                "optimizations": ["Use uint256 instead of uint"],
                "estimated_cost": 50000
            },
            "general_analysis": {
                "code_quality": 90,
                "maintainability": 85,
                "comments": ["Well-structured contract"]
            }
        }
        
        request_data = {
            "contract_code": sample_contract,
            "analysis_type": "comprehensive"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "security_analysis" in data
        assert "gas_analysis" in data
        assert "general_analysis" in data
        assert "analyzed_at" in data
        
        # Verify security analysis
        security = data["security_analysis"]
        assert security["score"] == 85
        assert isinstance(security["vulnerabilities"], list)
        assert isinstance(security["recommendations"], list)
        
        # Verify gas analysis
        gas = data["gas_analysis"]
        assert gas["score"] == 75
        assert isinstance(gas["optimizations"], list)
        assert isinstance(gas["estimated_cost"], int)
        
        # Verify general analysis
        general = data["general_analysis"]
        assert general["code_quality"] == 90
        assert general["maintainability"] == 85
        assert isinstance(general["comments"], list)
    
    @pytest.mark.asyncio
    @patch('main.GeminiService.analyze_contract')
    async def test_analyze_contract_security_only(self, mock_analyze, async_client, sample_contract):
        """Test contract analysis with security focus only."""
        mock_analyze.return_value = {
            "security_analysis": {
                "score": 92,
                "vulnerabilities": [],
                "recommendations": ["Add access control modifiers"]
            }
        }
        
        request_data = {
            "contract_code": sample_contract,
            "analysis_type": "security"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "security_analysis" in data
        assert "gas_analysis" not in data  # Should not include gas analysis
        assert "general_analysis" not in data  # Should not include general analysis
    
    @pytest.mark.asyncio
    @patch('main.GeminiService.generate_contract')
    async def test_generate_contract_with_valid_requirements(self, mock_generate, async_client):
        """Test contract generation with valid requirements."""
        mock_generate.return_value = {
            "contract_code": "pragma solidity ^0.8.0;\n\ncontract GeneratedToken {\n    // Generated code\n}",
            "explanation": "This contract implements a basic ERC-20 token with minting functionality.",
            "features": ["ERC-20 compliant", "Minting capability", "Access control"],
            "security_notes": ["Uses OpenZeppelin contracts", "Implements proper access control"]
        }
        
        request_data = {
            "requirements": "Create an ERC-20 token with minting functionality",
            "contract_type": "token",
            "features": ["minting", "access_control"]
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "contract_code" in data
        assert "explanation" in data
        assert "features" in data
        assert "security_notes" in data
        assert "generated_at" in data
        
        # Verify content
        assert "pragma solidity" in data["contract_code"]
        assert isinstance(data["features"], list)
        assert isinstance(data["security_notes"], list)
    
    @pytest.mark.asyncio
    async def test_analyze_contract_with_invalid_json(self, async_client):
        """Test contract analysis with invalid JSON payload."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json={"invalid": "payload"})
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_generate_contract_with_invalid_json(self, async_client):
        """Test contract generation with invalid JSON payload."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json={"invalid": "payload"})
        
        assert response.status_code == 422

class TestGeminiService:
    """Test suite for GeminiService integration."""
    
    @pytest.fixture
    def gemini_service(self):
        """Create a GeminiService instance for testing."""
        return GeminiService()
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_service_initialization(self, mock_model, gemini_service):
        """Test GeminiService initializes correctly."""
        assert gemini_service.model_name == "gemini-1.5-flash"
        mock_model.assert_called_once_with("gemini-1.5-flash")
    
    @pytest.mark.asyncio
    @patch('main.GeminiService._call_gemini')
    async def test_analyze_contract_security_analysis(self, mock_call, gemini_service, sample_contract):
        """Test security analysis functionality."""
        mock_call.return_value = """
        {
            "security_score": 85,
            "vulnerabilities": ["Potential reentrancy in line 25"],
            "recommendations": ["Add ReentrancyGuard", "Use checks-effects-interactions pattern"]
        }
        """
        
        result = await gemini_service.analyze_contract(sample_contract, "security")
        
        assert "security_analysis" in result
        security = result["security_analysis"]
        assert security["score"] == 85
        assert len(security["vulnerabilities"]) == 1
        assert len(security["recommendations"]) == 2
    
    @pytest.mark.asyncio
    @patch('main.GeminiService._call_gemini')
    async def test_analyze_contract_gas_analysis(self, mock_call, gemini_service, sample_contract):
        """Test gas optimization analysis."""
        mock_call.return_value = """
        {
            "gas_score": 75,
            "optimizations": ["Use uint256 instead of uint", "Pack struct variables"],
            "estimated_cost": 45000
        }
        """
        
        result = await gemini_service.analyze_contract(sample_contract, "gas")
        
        assert "gas_analysis" in result
        gas = result["gas_analysis"]
        assert gas["score"] == 75
        assert len(gas["optimizations"]) == 2
        assert gas["estimated_cost"] == 45000
    
    @pytest.mark.asyncio
    @patch('main.GeminiService._call_gemini')
    async def test_generate_contract_functionality(self, mock_call, gemini_service):
        """Test contract generation functionality."""
        mock_call.return_value = """
        pragma solidity ^0.8.0;
        
        import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
        import "@openzeppelin/contracts/access/Ownable.sol";
        
        contract GeneratedToken is ERC20, Ownable {
            constructor() ERC20("Generated", "GEN") {}
            
            function mint(address to, uint256 amount) public onlyOwner {
                _mint(to, amount);
            }
        }
        """
        
        requirements = "Create an ERC-20 token with minting functionality"
        result = await gemini_service.generate_contract(requirements, "token", ["minting"])
        
        assert "contract_code" in result
        assert "pragma solidity" in result["contract_code"]
        assert "explanation" in result
        assert "features" in result
        assert "security_notes" in result
    
    def test_create_security_prompt(self, gemini_service, sample_contract):
        """Test security analysis prompt creation."""
        prompt = gemini_service._create_security_prompt(sample_contract)
        
        assert "security vulnerabilities" in prompt.lower()
        assert "smart contract" in prompt.lower()
        assert sample_contract in prompt
        assert "json format" in prompt.lower()
    
    def test_create_gas_prompt(self, gemini_service, sample_contract):
        """Test gas optimization prompt creation."""
        prompt = gemini_service._create_gas_prompt(sample_contract)
        
        assert "gas optimization" in prompt.lower()
        assert "efficiency" in prompt.lower()
        assert sample_contract in prompt
        assert "json format" in prompt.lower()
    
    def test_create_generation_prompt(self, gemini_service):
        """Test contract generation prompt creation."""
        requirements = "Create a simple token contract"
        contract_type = "token"
        features = ["minting", "burning"]
        
        prompt = gemini_service._create_generation_prompt(requirements, contract_type, features)
        
        assert requirements in prompt
        assert contract_type in prompt
        assert "minting" in prompt
        assert "burning" in prompt
        assert "solidity" in prompt.lower()

class TestAIServiceErrorHandling:
    """Test error handling in AI service."""
    
    @pytest.mark.asyncio
    @patch('main.GeminiService.analyze_contract')
    async def test_analyze_contract_gemini_api_error(self, mock_analyze, async_client, sample_contract):
        """Test handling of Gemini API errors during analysis."""
        mock_analyze.side_effect = Exception("Gemini API error")
        
        request_data = {
            "contract_code": sample_contract,
            "analysis_type": "security"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        assert response.status_code == 500
        error_data = response.json()
        assert "error" in error_data
    
    @pytest.mark.asyncio
    @patch('main.GeminiService.generate_contract')
    async def test_generate_contract_gemini_api_error(self, mock_generate, async_client):
        """Test handling of Gemini API errors during generation."""
        mock_generate.side_effect = Exception("Gemini API error")
        
        request_data = {
            "requirements": "Create a token contract",
            "contract_type": "token"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 500
        error_data = response.json()
        assert "error" in error_data
    
    @pytest.mark.asyncio
    async def test_analyze_with_missing_required_field(self, async_client):
        """Test analysis request with missing required field."""
        request_data = {
            "analysis_type": "security"
            # Missing contract_code field
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_generate_with_missing_requirements(self, async_client):
        """Test generation request with missing requirements."""
        request_data = {
            "contract_type": "token"
            # Missing requirements field
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_analysis_type(self, async_client, sample_contract):
        """Test analysis with invalid analysis type."""
        request_data = {
            "contract_code": sample_contract,
            "analysis_type": "invalid_type"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        # Should return validation error for invalid enum value
        assert response.status_code == 422

class TestAIServiceIntegration:
    """Integration tests for AI service."""
    
    @pytest.mark.asyncio
    @patch('main.GeminiService.analyze_contract')
    async def test_analyze_contract_performance(self, mock_analyze, async_client, sample_contract):
        """Test that contract analysis completes within reasonable time."""
        import time
        
        # Mock quick response
        mock_analyze.return_value = {"security_analysis": {"score": 85}}
        
        request_data = {
            "contract_code": sample_contract,
            "analysis_type": "security"
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/analyze", json=request_data)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        # Should complete quickly with mocked service
        assert duration < 2.0
    
    @pytest.mark.asyncio
    @patch('main.GeminiService.analyze_contract')
    async def test_concurrent_analysis_requests(self, mock_analyze, async_client, sample_contract):
        """Test handling multiple concurrent analysis requests."""
        import asyncio
        
        mock_analyze.return_value = {"security_analysis": {"score": 85}}
        
        request_data = {
            "contract_code": sample_contract,
            "analysis_type": "security"
        }
        
        async def make_request():
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                return await client.post("/analyze", json=request_data)
        
        # Execute 3 concurrent requests
        tasks = [make_request() for _ in range(3)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200