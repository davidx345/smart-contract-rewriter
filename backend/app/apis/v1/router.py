from fastapi import APIRouter
from .endpoints import contracts

api_router_v1 = APIRouter()
api_router_v1.include_router(contracts.router, prefix="/contracts", tags=["contracts"])

@api_router_v1.get("/")
async def read_v1_root():
    return {"message": "API v1"}
