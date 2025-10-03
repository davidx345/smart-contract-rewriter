"""
Pytest configuration and shared fixtures for the Smart Contract Rewriter Platform tests.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
import httpx
import os
from unittest.mock import Mock, AsyncMock

# Test configuration
pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    test_env = {
        "GEMINI_API_KEY": "test_gemini_key_12345",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
        "SECRET_KEY": "test_secret_key_minimum_32_characters_long",
        "REDIS_URL": "redis://localhost:6379/1",
        "DEBUG": "true",
        "ENVIRONMENT": "test"
    }
    
    # Set environment variables
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Clean up
    for key in test_env.keys():
        os.environ.pop(key, None)

@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with httpx.AsyncClient() as client:
        yield client

@pytest.fixture
def sample_contract():
    """Sample Solidity contract for testing."""
    return """
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 private value;
    
    event ValueChanged(uint256 newValue);
    
    function setValue(uint256 _value) public {
        value = _value;
        emit ValueChanged(_value);
    }
    
    function getValue() public view returns (uint256) {
        return value;
    }
}
"""

@pytest.fixture
def sample_vulnerable_contract():
    """Sample contract with known vulnerabilities for testing."""
    return """
pragma solidity ^0.8.0;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    
    function withdraw() public {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        // Vulnerable to reentrancy attack
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0;
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
}
"""

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini AI response for testing."""
    return {
        "vulnerabilities": [
            {
                "type": "reentrancy",
                "severity": "High",
                "line_number": 8,
                "description": "Potential reentrancy vulnerability in withdraw function",
                "recommendation": "Use checks-effects-interactions pattern or add reentrancy guard"
            }
        ],
        "gas_optimizations": [
            {
                "function_name": "withdraw",
                "issue": "Multiple state reads",
                "recommendation": "Cache balance in memory",
                "estimated_savings": "15%"
            }
        ],
        "code_quality": {
            "score": 75,
            "issues": ["Missing input validation", "No access control"],
            "suggestions": ["Add modifier for access control", "Validate inputs"]
        },
        "summary": "Contract has critical reentrancy vulnerability that should be fixed immediately"
    }

@pytest.fixture
def mock_contract_analysis_result():
    """Mock contract analysis result for testing."""
    return {
        "contract_name": "TestContract",
        "security_score": 85,
        "issues": [
            {
                "severity": "medium",
                "type": "gas_optimization",
                "line": 15,
                "description": "Consider using uint256 instead of uint for gas optimization"
            }
        ],
        "suggestions": [
            "Add input validation",
            "Use OpenZeppelin contracts for standard implementations"
        ],
        "analyzed_at": "2024-01-01T12:00:00Z"
    }

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    service = Mock()
    service.analyze_contract = AsyncMock()
    service.generate_contract = AsyncMock()
    return service

@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    db = Mock()
    db.execute = AsyncMock()
    db.fetch = AsyncMock()
    db.fetchrow = AsyncMock()
    return db

class TestClient:
    """Test client wrapper for microservices."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def post(self, endpoint: str, json_data: dict = None, **kwargs):
        """Make async POST request."""
        return await self.client.post(endpoint, json=json_data, **kwargs)
    
    async def get(self, endpoint: str, **kwargs):
        """Make async GET request."""
        return await self.client.get(endpoint, **kwargs)
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()

@pytest.fixture
async def contract_service_client():
    """Test client for contract service."""
    client = TestClient("http://localhost:8002")
    yield client
    await client.close()

@pytest.fixture
async def ai_service_client():
    """Test client for AI service."""
    client = TestClient("http://localhost:8003")
    yield client
    await client.close()

@pytest.fixture
async def auth_service_client():
    """Test client for auth service."""
    client = TestClient("http://localhost:8001")
    yield client
    await client.close()

# Test data
VALID_TEST_CONTRACTS = [
    """
pragma solidity ^0.8.0;
contract BasicToken {
    mapping(address => uint256) public balances;
    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
""",
    """
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
contract MyToken is ERC20 {
    constructor() ERC20("MyToken", "MTK") {}
}
"""
]

INVALID_TEST_CONTRACTS = [
    "not a solidity contract",
    "",
    "pragma solidity ^0.8.0; contract {", # Invalid syntax
]