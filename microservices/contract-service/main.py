"""
Contract Analysis Microservice
Handles smart contract analysis, storage, and retrieval
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import json
from datetime import datetime

# Contract Models
class ContractAnalyzeRequest(BaseModel):
    contract_code: str
    contract_name: Optional[str] = None

class ContractAnalysisResult(BaseModel):
    contract_name: str
    security_score: int
    issues: List[dict]
    suggestions: List[str]
    analyzed_at: str

# Initialize FastAPI app
app = FastAPI(
    title="SoliVolt Contract Service",
    description="Smart contract analysis and management microservice",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://smart-contract-rewriter.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Contract Analysis Endpoints
@app.post("/analyze", response_model=ContractAnalysisResult)
async def analyze_contract(request: ContractAnalyzeRequest):
    """Analyze smart contract for security issues"""
    try:
        # Simulate analysis (replace with actual AI analysis)
        analysis = {
            "contract_name": request.contract_name or "Unknown",
            "security_score": 85,
            "issues": [
                {
                    "severity": "medium",
                    "type": "reentrancy",
                    "line": 45,
                    "description": "Potential reentrancy vulnerability"
                }
            ],
            "suggestions": [
                "Add reentrancy guard",
                "Optimize gas usage"
            ],
            "analyzed_at": datetime.utcnow().isoformat()
        }
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "contract-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SoliVolt Contract Service",
        "version": "1.0.0",
        "endpoints": {
            "contracts": "/api/v1/contracts/*",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
