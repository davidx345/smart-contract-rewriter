"""
Unified Smart Contract Rewriter API
Combines authentication and contract analysis in a single FastAPI app
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from typing import Optional, List
import tempfile

# Add backend path for imports
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.append(backend_path)

# Create main application
app = FastAPI(
    title="Smart Contract Rewriter API",
    description="Unified API for authentication and smart contract analysis",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://smart-contract-rewriter.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Auth Models
class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Contract Models
class ContractAnalyzeRequest(BaseModel):
    contract_code: str
    contract_name: Optional[str] = None

class RewriteRequest(BaseModel):
    contract_code: str
    requirements: Optional[str] = None

# Dummy user store (replace with real database in production)
fake_users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "full_name": "Test User",
        "hashed_password": "fakehashedpassword"
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Simple check for demo (use proper hashing in production)
    return plain_password == "password" or hashed_password == "fakehashedpassword"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Smart Contract Rewriter API",
        "version": "1.0.0",
        "frontend": "https://smart-contract-rewriter.vercel.app",
        "endpoints": {
            "auth": "/auth/*",
            "contracts": "/contracts/*",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": ["auth", "contracts"]
    }

# Authentication Endpoints
@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = fake_users_db.get(user_data.email)
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    if user_data.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Add user to fake database
    fake_users_db[user_data.email] = {
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": "fakehashedpassword"  # Hash properly in production
    }
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def get_me(current_user: str = Depends(get_current_user)):
    user = fake_users_db.get(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"email": user["email"], "full_name": user["full_name"]}

# Contract Analysis Endpoints
@app.post("/contracts/analyze")
async def analyze_contract(
    request: ContractAnalyzeRequest,
    current_user: str = Depends(get_current_user)
):
    """Analyze smart contract for security issues and optimization opportunities"""
    try:
        # Simple analysis logic (replace with actual AI analysis)
        analysis = {
            "contract_name": request.contract_name or "Unknown",
            "security_score": 85,
            "issues": [
                {
                    "severity": "medium",
                    "type": "reentrancy",
                    "line": 45,
                    "description": "Potential reentrancy vulnerability in withdrawal function"
                },
                {
                    "severity": "low", 
                    "type": "gas_optimization",
                    "line": 23,
                    "description": "Use of storage when memory would be more efficient"
                }
            ],
            "suggestions": [
                "Add reentrancy guard to withdrawal functions",
                "Optimize storage usage in loops",
                "Consider using events for better transparency"
            ],
            "analyzed_by": current_user,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/contracts/rewrite")
async def rewrite_contract(
    request: RewriteRequest,
    current_user: str = Depends(get_current_user)
):
    """Rewrite smart contract based on analysis and requirements"""
    try:
        # Simple rewrite logic (replace with actual AI rewriting)
        rewritten_code = f"""// Rewritten Smart Contract
// Original issues addressed
// Optimized by: {current_user}

pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract OptimizedContract is ReentrancyGuard {{
    // Your optimized contract code here
    // - Added reentrancy protection
    // - Optimized gas usage
    // - Enhanced security measures
    
    {request.contract_code.split('contract')[1] if 'contract' in request.contract_code else '// Original contract logic here'}
}}"""
        
        return {
            "success": True,
            "rewritten_code": rewritten_code,
            "improvements": [
                "Added ReentrancyGuard protection",
                "Optimized storage access patterns", 
                "Enhanced error handling",
                "Added comprehensive events"
            ],
            "rewritten_by": current_user,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewrite failed: {str(e)}")

@app.post("/contracts/upload")
async def upload_contract(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    """Upload and analyze a smart contract file"""
    try:
        # Read file content
        content = await file.read()
        contract_code = content.decode('utf-8')
        
        # Basic validation
        if not contract_code.strip():
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Analyze the uploaded contract
        analysis_request = ContractAnalyzeRequest(
            contract_code=contract_code,
            contract_name=file.filename
        )
        
        return await analyze_contract(analysis_request, current_user)
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a text file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/contracts/history")
async def get_contract_history(current_user: str = Depends(get_current_user)):
    """Get user's contract analysis history"""
    # Mock history data (replace with database query)
    return {
        "contracts": [
            {
                "id": 1,
                "name": "MyToken.sol",
                "analyzed_at": "2024-01-15T10:30:00Z",
                "security_score": 92,
                "status": "completed"
            },
            {
                "id": 2,
                "name": "DEX.sol", 
                "analyzed_at": "2024-01-14T15:45:00Z",
                "security_score": 78,
                "status": "completed"
            }
        ],
        "total": 2
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Smart Contract Rewriter API on port {port}")
    uvicorn.run("unified_main:app", host="0.0.0.0", port=port)
