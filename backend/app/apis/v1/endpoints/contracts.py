from fastapi import APIRouter, HTTPException, Depends, Body, BackgroundTasks, Request
from typing import Any, List
from sqlalchemy.orm import Session
import datetime

from app.models.contract_models import ( # Pydantic models for request/response
    ContractInput, 
    ContractOutput, 
    OptimizationRequest, 
    ContractHistoryResponse, # Renamed for clarity if it's a response model
    AnalysisReport, # Assuming this is part of ContractOutput or a separate response
    RewriteReport # Assuming this is part of ContractOutput or a separate response
)
from app.services.contract_processing_service import contract_service
from app.services.metrics_service import metrics_service
from app.db.session import get_db
from app.schemas.contract_db_schemas import ContractAnalysisDB, ContractRewriteDB # SQLAlchemy models

router = APIRouter()

@router.post("/analyze", response_model=ContractOutput)
@metrics_service.processing_time("analysis")
async def analyze_contract(
    request: Request,
    contract_input: ContractInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Analyze a smart contract for vulnerabilities, gas inefficiencies, and code quality.
    Stores the analysis result in the database.
    """
    try:
        # Track the analysis request
        metrics_service.track_contract_analysis("started", "solidity")
        
        # Perform the analysis using the service
        analysis_result: ContractOutput = await contract_service.process_contract_analysis(contract_input)
        
        # Track successful analysis
        metrics_service.track_contract_analysis("success", "solidity")
        
        # Log the analysis to the database in the background
        background_tasks.add_task(
            log_analysis_to_db, 
            db=db, 
            contract_input=contract_input, 
            analysis_result=analysis_result,
            success=True
        )
        return analysis_result
    except Exception as e:
        # Track failed analysis
        metrics_service.track_contract_analysis("failed", "solidity")
        metrics_service.track_error("analysis_error", "contract_endpoint")
        
        # Log failure attempt if needed, or handle more gracefully
        background_tasks.add_task(
            log_analysis_to_db, 
            db=db, 
            contract_input=contract_input, 
            analysis_result=None, # No result on failure
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error analyzing contract: {str(e)}")

@router.post("/rewrite", response_model=ContractOutput)
async def rewrite_contract(
    optimization_request: OptimizationRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Rewrite and optimize a smart contract based on specified goals.
    Stores the rewrite result in the database.
    """
    try:
        # Perform the optimization using the service
        rewrite_result: ContractOutput = await contract_service.process_contract_optimization(optimization_request)
        
        # Log the optimization to the database in the background
        background_tasks.add_task(
            log_rewrite_to_db, 
            db=db, 
            optimization_request=optimization_request, 
            rewrite_result=rewrite_result,
            success=True
        )
        return rewrite_result
    except Exception as e:
        background_tasks.add_task(
            log_rewrite_to_db, 
            db=db, 
            optimization_request=optimization_request, 
            rewrite_result=None,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error rewriting contract: {str(e)}")

@router.get("/history", response_model=List[ContractHistoryResponse])
async def get_contract_history(
    db: Session = Depends(get_db),
    skip: int = 0, 
    limit: int = 100
) -> Any:
    """
    Get history of contract analyses and rewrites from the database.
    """
    # Fetch both analyses and rewrites, then combine and sort them if necessary
    # This is a simplified example; you might want separate endpoints or more complex querying
    
    analyses_db = db.query(ContractAnalysisDB).order_by(ContractAnalysisDB.requested_at.desc()).offset(skip).limit(limit).all()
    rewrites_db = db.query(ContractRewriteDB).order_by(ContractRewriteDB.requested_at.desc()).offset(skip).limit(limit).all()
    
    history_items = []
    for analysis_db in analyses_db:
        history_items.append(ContractHistoryResponse(
            id=str(analysis_db.id),
            type="analysis",
            contract_name=analysis_db.contract_name,
            timestamp=analysis_db.requested_at.isoformat(),
            success=analysis_db.analysis_report is not None, # Or a dedicated success field
            details={"analysis_report": analysis_db.analysis_report}
        ))

    for rewrite_db in rewrites_db:
        history_items.append(ContractHistoryResponse(
            id=str(rewrite_db.id),
            type="rewrite",
            contract_name=rewrite_db.contract_name,
            timestamp=rewrite_db.requested_at.isoformat(),
            success=rewrite_db.rewritten_code is not None, # Or a dedicated success field
            optimization_goals=rewrite_db.optimization_goals,
            details={"rewrite_summary": rewrite_db.rewrite_summary}
        ))
        
    # Sort combined history by timestamp descending
    history_items.sort(key=lambda item: item.timestamp, reverse=True)
    
    return history_items[:limit] # Apply limit after combining and sorting

@router.get("/health")
async def contract_service_health() -> dict:
    """Health check for contract processing service"""
    return {
        "status": "healthy",
        "service": "contract_processing",
        "gemini_configured": bool(contract_service.gemini_service),
        "web3_configured": bool(contract_service.web3_service)
    }

# --- Background Task Functions for DB Logging ---

def log_analysis_to_db(
    db: Session, 
    contract_input: ContractInput, 
    analysis_result: ContractOutput = None, 
    success: bool = False,
    error_message: str = None
):
    """Log contract analysis attempt and result to the database."""
    try:
        db_analysis = ContractAnalysisDB(
            contract_name=contract_input.contract_name,
            original_code=contract_input.source_code,
            analysis_report=analysis_result.analysis_report.model_dump() if success and analysis_result and analysis_result.analysis_report else {"error": error_message or "Analysis failed"},
            vulnerabilities_found=[v.model_dump() for v in analysis_result.vulnerabilities] if success and analysis_result and analysis_result.vulnerabilities else None,
            gas_analysis=analysis_result.gas_analysis.model_dump() if success and analysis_result and analysis_result.gas_analysis else None,
            requested_at=datetime.datetime.now(datetime.timezone.utc),
            completed_at=datetime.datetime.now(datetime.timezone.utc) if success else None
            # user_id can be added if you have user authentication
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        print(f"Logged analysis for {contract_input.contract_name} to DB. ID: {db_analysis.id}, Success: {success}")
    except Exception as e:
        db.rollback()
        print(f"DB Error logging analysis for {contract_input.contract_name}: {e}")

def log_rewrite_to_db(
    db: Session, 
    optimization_request: OptimizationRequest, 
    rewrite_result: ContractOutput = None, 
    success: bool = False,
    error_message: str = None
):
    """Log contract rewrite attempt and result to the database."""
    try:
        db_rewrite = ContractRewriteDB(
            contract_name=optimization_request.contract_name,
            original_code=optimization_request.source_code,
            rewritten_code=rewrite_result.rewritten_code if success and rewrite_result else None,
            optimization_goals=[goal.value for goal in optimization_request.optimization_goals],
            rewrite_summary=rewrite_result.rewrite_report.model_dump() if success and rewrite_result and rewrite_result.rewrite_report else {"error": error_message or "Rewrite failed"},
            requested_at=datetime.datetime.now(datetime.timezone.utc),
            completed_at=datetime.datetime.now(datetime.timezone.utc) if success else None
            # user_id and analysis_id can be added if applicable
        )
        db.add(db_rewrite)
        db.commit()
        db.refresh(db_rewrite)
        print(f"Logged rewrite for {optimization_request.contract_name} to DB. ID: {db_rewrite.id}, Success: {success}")
    except Exception as e:
        db.rollback()
        print(f"DB Error logging rewrite for {optimization_request.contract_name}: {e}")

@router.post("/analyze/raw")
async def analyze_contract_raw(request: Request):
    body = await request.body()
    print("/analyze/raw RAW BODY:", body)
    return {"received": body.decode()}
