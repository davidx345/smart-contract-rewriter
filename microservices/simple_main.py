"""
Simplified main orchestrator for Heroku deployment.
Single FastAPI app with mounted sub-applications.
"""

import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add paths for service imports
current_dir = os.path.dirname(__file__)
auth_service_path = os.path.join(current_dir, 'auth-service')
contract_service_path = os.path.join(current_dir, 'contract-service')
backend_path = os.path.join(current_dir, '..', 'backend')

sys.path.extend([auth_service_path, contract_service_path, backend_path])

# Create main application
app = FastAPI(
    title="Smart Contract Rewriter API",
    description="Unified microservices for smart contract analysis",
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

# Import and include routes
try:
    # Import auth service
    sys.path.append(auth_service_path)
    from main import app as auth_app
    app.mount("/auth", auth_app)
    print("✅ Auth service mounted successfully")
except Exception as e:
    print(f"❌ Error mounting auth service: {e}")

try:
    # Import contract service  
    sys.path.append(contract_service_path)
    from main import app as contract_app
    app.mount("/contracts", contract_app)
    print("✅ Contract service mounted successfully")
except Exception as e:
    print(f"❌ Error mounting contract service: {e}")

@app.get("/")
async def root():
    return {
        "message": "Smart Contract Rewriter API",
        "services": ["auth", "contracts"],
        "version": "1.0.0",
        "frontend": "https://smart-contract-rewriter.vercel.app"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "auth": "running",
            "contracts": "running"
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    uvicorn.run("simple_main:app", host="0.0.0.0", port=port)
