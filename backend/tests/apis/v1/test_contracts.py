import pytest
from httpx import AsyncClient

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Smart Contract Rewriter API"}

async def test_analyze_contract_success(client: AsyncClient):
    payload = {
        "contract_name": "TestContract",
        "code": "pragma solidity ^0.8.0; contract TestContract { uint256 public myNumber = 1; }"
    }
    response = await client.post("/api/v1/contracts/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["original_contract"] == payload["code"]
    assert "analysis_report" in data
    assert data["message"] == "Analysis complete (simulated)."

async def test_analyze_contract_empty_code(client: AsyncClient):
    payload = {
        "contract_name": "EmptyTest",
        "code": ""
    }
    response = await client.post("/api/v1/contracts/analyze", json=payload)
    assert response.status_code == 200 # Or 422 if you add validation for non-empty code
    # Depending on how your service handles empty code, adjust assertions
    data = response.json()
    assert data["message"] == "Analysis complete (simulated)."

async def test_rewrite_contract_success(client: AsyncClient):
    payload = {
        "contract_name": "RewriteTest",
        "code": "pragma solidity ^0.8.0; contract RewriteTest { function inefficient() public view returns (uint) { uint sum = 0; for(uint i=0; i<10; i++){ sum += i;} return sum;} }",
        "optimization_goals": ["gas_efficiency", "security_hardening"]
    }
    response = await client.post("/api/v1/contracts/rewrite", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["original_contract"] == payload["code"]
    assert "rewritten_contract" in data
    assert "analysis_report" in data
    assert data["message"] == "Contract rewritten and optimized (simulated)."
    assert "gas_efficiency" in data["analysis_report"]["optimizations_applied"]

# Add more tests for edge cases, error handling, different inputs, etc.
