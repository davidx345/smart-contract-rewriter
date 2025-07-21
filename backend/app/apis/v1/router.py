from fastapi import APIRouter
from .endpoints import contracts, auth, enterprise, clean_architecture, security

api_router_v1 = APIRouter()
api_router_v1.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router_v1.include_router(auth.router, tags=["authentication"])
api_router_v1.include_router(enterprise.router, prefix="/enterprise", tags=["enterprise"])
api_router_v1.include_router(clean_architecture.router, prefix="/clean", tags=["clean-architecture"])
api_router_v1.include_router(security.router, prefix="/security", tags=["security"])

@api_router_v1.get("/")
async def read_v1_root():
    return {"message": "SoliVolt API v1 - Enterprise Smart Contract Platform with Advanced Security"}
