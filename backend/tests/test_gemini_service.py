# filepath: backend/tests/test_gemini_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.gemini_service import GeminiService
from app.models.contract_models import OptimizationGoal

@pytest.mark.asyncio
class TestGeminiService:
    
    @pytest.fixture
    def gemini_service(self):
        return GeminiService()
    
    async def test_analyze_contract_success(self, gemini_service):
        """Test successful contract analysis with Gemini"""
        contract_code = """
        pragma solidity ^0.8.0;
        contract SimpleStorage {
            uint256 private storedData;
            function set(uint256 x) public { storedData = x; }
            function get() public view returns (uint256) { return storedData; }
        }
        """
        
        mock_response = {
            "vulnerabilities": [
                {
                    "type": "REENTRANCY",
                    "severity": "MEDIUM",
                    "description": "Potential reentrancy in set function",
                    "line_number": 4,
                    "suggestion": "Add reentrancy guard"
                }
            ],
            "optimization_suggestions": [
                {
                    "type": "GAS_OPTIMIZATION",
                    "description": "Use external instead of public for set function",
                    "potential_savings": 200
                }
            ],
            "security_score": 8.5,
            "code_quality_metrics": {
                "complexity": "LOW",
                "maintainability": "HIGH",
                "test_coverage": "UNKNOWN"
            }
        }
        
        with patch.object(gemini_service, '_call_gemini_api') as mock_api:
            mock_api.return_value = mock_response
            
            result = await gemini_service.analyze_contract(contract_code, "SimpleStorage")
            
            assert result["security_score"] == 8.5
            assert len(result["vulnerabilities"]) == 1
            assert result["vulnerabilities"][0]["type"] == "REENTRANCY"
            assert len(result["optimization_suggestions"]) == 1
    
    async def test_rewrite_contract_success(self, gemini_service):
        """Test successful contract rewriting with Gemini"""
        contract_code = """
        pragma solidity ^0.8.0;
        contract SimpleStorage {
            uint256 private storedData;
            function set(uint256 x) public { storedData = x; }
            function get() public view returns (uint256) { return storedData; }
        }
        """
        
        optimization_goals = [OptimizationGoal.GAS_OPTIMIZATION, OptimizationGoal.SECURITY_ENHANCEMENT]
        
        mock_response = {
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
                    "description": "Changed uint256 to uint32",
                    "line_number": 3
                }
            ],
            "explanation": "Optimized for gas usage and security"
        }
        
        with patch.object(gemini_service, '_call_gemini_api') as mock_api:
            mock_api.return_value = mock_response
            
            result = await gemini_service.rewrite_contract(
                contract_code, "SimpleStorage", optimization_goals
            )
            
            assert "rewritten_contract" in result
            assert len(result["changes_made"]) == 1
            assert "uint32" in result["rewritten_contract"]
    
    async def test_call_gemini_api_success(self, gemini_service):
        """Test successful Gemini API call"""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"test": "response"}'
        mock_model.generate_content_async.return_value = mock_response
        
        with patch('google.generativeai.GenerativeModel') as mock_gen_model:
            mock_gen_model.return_value = mock_model
            
            result = await gemini_service._call_gemini_api("test prompt")
            
            assert result == {"test": "response"}
            mock_model.generate_content_async.assert_called_once()
    
    async def test_call_gemini_api_invalid_json(self, gemini_service):
        """Test Gemini API call with invalid JSON response"""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = 'invalid json response'
        mock_model.generate_content_async.return_value = mock_response
        
        with patch('google.generativeai.GenerativeModel') as mock_gen_model:
            mock_gen_model.return_value = mock_model
            
            result = await gemini_service._call_gemini_api("test prompt")
            
            # Should return fallback response for invalid JSON
            assert "error" in result
            assert result["error"] == "Failed to parse JSON response"
    
    async def test_call_gemini_api_exception(self, gemini_service):
        """Test Gemini API call with exception"""
        mock_model = MagicMock()
        mock_model.generate_content_async.side_effect = Exception("API Error")
        
        with patch('google.generativeai.GenerativeModel') as mock_gen_model:
            mock_gen_model.return_value = mock_model
            
            with pytest.raises(Exception):
                await gemini_service._call_gemini_api("test prompt")
    
    def test_extract_json_from_text_success(self, gemini_service):
        """Test successful JSON extraction from text"""
        text_with_json = '''
        Here is some text before
        ```json
        {"test": "value", "number": 123}
        ```
        Some text after
        '''
        
        result = gemini_service._extract_json_from_text(text_with_json)
        assert result == {"test": "value", "number": 123}
    
    def test_extract_json_from_text_plain_json(self, gemini_service):
        """Test JSON extraction from plain JSON text"""
        json_text = '{"simple": "json"}'
        
        result = gemini_service._extract_json_from_text(json_text)
        assert result == {"simple": "json"}
    
    def test_extract_json_from_text_invalid(self, gemini_service):
        """Test JSON extraction with invalid JSON"""
        invalid_text = "This is not JSON at all"
        
        result = gemini_service._extract_json_from_text(invalid_text)
        assert result is None
    
    def test_get_analysis_fallback_response(self, gemini_service):
        """Test analysis fallback response"""
        result = gemini_service._get_analysis_fallback_response()
        
        assert "vulnerabilities" in result
        assert "optimization_suggestions" in result
        assert "security_score" in result
        assert result["security_score"] == 5.0
    
    def test_get_rewrite_fallback_response(self, gemini_service):
        """Test rewrite fallback response"""
        original_code = "pragma solidity ^0.8.0; contract Test {}"
        
        result = gemini_service._get_rewrite_fallback_response(original_code)
        
        assert "rewritten_contract" in result
        assert "changes_made" in result
        assert "explanation" in result
        assert result["rewritten_contract"] == original_code
    
    def test_create_analysis_prompt(self, gemini_service):
        """Test analysis prompt creation"""
        contract_code = "contract Test {}"
        contract_name = "TestContract"
        
        prompt = gemini_service._create_analysis_prompt(contract_code, contract_name)
        
        assert contract_code in prompt
        assert contract_name in prompt
        assert "ANALYZE THIS SOLIDITY CONTRACT" in prompt
        assert "vulnerabilities" in prompt.lower()
    
    def test_create_rewrite_prompt(self, gemini_service):
        """Test rewrite prompt creation"""
        contract_code = "contract Test {}"
        contract_name = "TestContract"
        optimization_goals = [OptimizationGoal.GAS_OPTIMIZATION]
        
        prompt = gemini_service._create_rewrite_prompt(
            contract_code, contract_name, optimization_goals
        )
        
        assert contract_code in prompt
        assert contract_name in prompt
        assert "REWRITE THIS SOLIDITY CONTRACT" in prompt
        assert "GAS_OPTIMIZATION" in prompt
