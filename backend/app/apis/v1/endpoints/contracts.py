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
from app.schemas.contract_db_schemas import ContractAnalysisDB, ContractRewriteDB, ContractGenerationDB # SQLAlchemy models

router = APIRouter()

@router.post("/analyze", response_model=ContractOutput)
@metrics_service.processing_time("analysis")
async def analyze_contract(
    request: Request,
    contract_input: ContractInput = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
) -> Any:
    print("/analyze RAW BODY:", await request.body())  # Log the raw request body for debugging
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
    Get history of contract analyses, rewrites, and generations from the database.
    """
    # Fetch analyses, rewrites, and generations, then combine and sort them
    
    analyses_db = db.query(ContractAnalysisDB).order_by(ContractAnalysisDB.requested_at.desc()).offset(skip).limit(limit).all()
    rewrites_db = db.query(ContractRewriteDB).order_by(ContractRewriteDB.requested_at.desc()).offset(skip).limit(limit).all()
    generations_db = db.query(ContractGenerationDB).order_by(ContractGenerationDB.requested_at.desc()).offset(skip).limit(limit).all()
    
    history_items = []
    for analysis_db in analyses_db:
        # Extract analysis data for better frontend display
        analysis_data = analysis_db.analysis_report if isinstance(analysis_db.analysis_report, dict) else {}
        vulnerabilities_count = len(analysis_data.get("vulnerabilities", [])) if analysis_data else 0        
        history_items.append(ContractHistoryResponse(
            id=str(analysis_db.id),
            type="analysis",
            contract_name=analysis_db.contract_name,
            timestamp=analysis_db.requested_at,
            success=analysis_db.analysis_report is not None,
            details={
                "analysis_report": analysis_db.analysis_report,
                "original_code": analysis_db.original_code,
                "vulnerabilities_count": vulnerabilities_count,
                "gas_analysis": analysis_db.gas_analysis
            }
        ))

    for rewrite_db in rewrites_db:
        # Extract rewrite data for better frontend display
        rewrite_data = rewrite_db.rewrite_summary if isinstance(rewrite_db.rewrite_summary, dict) else {}
        
        # Calculate gas savings if available
        gas_savings_percentage = 0.0
        if rewrite_data and isinstance(rewrite_data, dict):
            analysis_data = rewrite_data.get("analysis_of_rewritten_code", {})
            if analysis_data:
                gas_savings_percentage = analysis_data.get("total_gas_savings_percentage", 0.0) or 0.0        
        history_items.append(ContractHistoryResponse(
            id=str(rewrite_db.id),
            type="rewrite",
            contract_name=rewrite_db.contract_name,
            timestamp=rewrite_db.requested_at,
            success=rewrite_db.rewritten_code is not None,
            optimization_goals=rewrite_db.optimization_goals,            details={
                "rewrite_summary": rewrite_db.rewrite_summary,
                "original_code": rewrite_db.original_code,
                "rewritten_code": rewrite_db.rewritten_code,
                "gas_savings_percentage": gas_savings_percentage,
                "optimization_goals": rewrite_db.optimization_goals,
                "changes_count": len(rewrite_data.get("changes_summary", [])) if rewrite_data else 0,
                # Add rewrite_report structure for frontend compatibility
                "rewrite_report": {
                    "rewritten_code": rewrite_db.rewritten_code,
                    "suggestions": rewrite_data.get("changes_summary", []) if rewrite_data else [],
                    "gas_optimization_details": {
                        "gas_savings_percentage": gas_savings_percentage
                    },
                    "security_improvements": rewrite_data.get("security_enhancements_made", []) if rewrite_data else []                } if rewrite_db.rewritten_code else None
            }
        ))
    
    # Process generated contracts
    for generation_db in generations_db:
        # Extract generation metadata
        generation_metadata = generation_db.generation_metadata if isinstance(generation_db.generation_metadata, dict) else {}
        
        history_items.append(ContractHistoryResponse(
            id=str(generation_db.id),
            type="generation",
            contract_name=generation_db.contract_name,
            timestamp=generation_db.requested_at,
            success=generation_db.generated_code is not None and generation_db.completed_at is not None,
            details={
                "generated_code": generation_db.generated_code,
                "description": generation_db.description,
                "features": generation_db.features,
                "generation_metadata": generation_metadata,
                "compiler_version": generation_db.compiler_version,
                "confidence_score": generation_metadata.get("confidence_score", 0.0),
                "generation_notes": generation_metadata.get("generation_notes", ""),
                "processing_time_seconds": generation_metadata.get("processing_time_seconds", 0.0)
            }
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
            vulnerabilities_found=[v.model_dump() for v in analysis_result.analysis_report.vulnerabilities] if success and analysis_result and analysis_result.analysis_report and analysis_result.analysis_report.vulnerabilities else None,
            gas_analysis=[gas.model_dump() for gas in analysis_result.analysis_report.gas_analysis_per_function] if success and analysis_result and analysis_result.analysis_report and analysis_result.analysis_report.gas_analysis_per_function else None,
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

def log_generation_to_db(
    db: Session,
    generation_request: dict,
    generation_result: ContractOutput = None,
    success: bool = False,
    error_message: str = None
):
    """Log contract generation attempt and result to the database."""
    try:
        from app.schemas.contract_db_schemas import ContractGenerationDB
        
        generation_metadata = {}
        if success and generation_result:
            generation_metadata = {
                "generation_notes": generation_result.generation_notes,
                "confidence_score": generation_result.confidence_score,
                "processing_time_seconds": generation_result.processing_time_seconds,
                "message": generation_result.message
            }
        elif error_message:
            generation_metadata = {
                "error": error_message,
                "generation_request": generation_request
            }
        
        db_generation = ContractGenerationDB(
            contract_name=generation_request.get("contract_name", "GeneratedContract"),
            description=generation_request.get("description", ""),
            features=generation_request.get("features", []),
            generated_code=generation_result.original_code if success and generation_result else "",
            generation_metadata=generation_metadata,
            compiler_version=generation_request.get("compiler_version", "0.8.19"),
            requested_at=datetime.datetime.now(datetime.timezone.utc),
            completed_at=datetime.datetime.now(datetime.timezone.utc) if success else None
        )
        db.add(db_generation)
        db.commit()
        db.refresh(db_generation)
        print(f"Logged generation for {generation_request.get('contract_name')} to DB. Success: {success}")
    except Exception as e:
        db.rollback()
        print(f"DB Error logging generation: {e}")

@router.post("/analyze/raw")
async def analyze_contract_raw(request: Request):
    body = await request.body()
    print("/analyze/raw RAW BODY:", body)
    return {"received": body.decode()}

@router.delete("/history/{contract_id}")
async def delete_contract_history(
    contract_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Delete a contract from history (both analysis and rewrite records).
    """
    try:
        # Convert contract_id to integer if it's numeric, handle both analysis and rewrite
        contract_id_int = int(contract_id)
        print(f"Attempting to delete contract with ID: {contract_id_int}")
        
        # Try to find and delete from analysis table
        analysis_deleted = False
        analysis_entry = db.query(ContractAnalysisDB).filter(ContractAnalysisDB.id == contract_id_int).first()
        if analysis_entry:
            print(f"Found analysis entry with ID: {contract_id_int}")
            db.delete(analysis_entry)
            analysis_deleted = True
          # Try to find and delete from rewrite table
        rewrite_deleted = False
        rewrite_entry = db.query(ContractRewriteDB).filter(ContractRewriteDB.id == contract_id_int).first()
        if rewrite_entry:
            print(f"Found rewrite entry with ID: {contract_id_int}")
            db.delete(rewrite_entry)
            rewrite_deleted = True
        
        # Try to find and delete from generation table
        generation_deleted = False
        generation_entry = db.query(ContractGenerationDB).filter(ContractGenerationDB.id == contract_id_int).first()
        if generation_entry:
            print(f"Found generation entry with ID: {contract_id_int}")
            db.delete(generation_entry)
            generation_deleted = True
        
        if not analysis_deleted and not rewrite_deleted and not generation_deleted:
            print(f"Contract with ID {contract_id_int} not found in any table")
            raise HTTPException(status_code=404, detail=f"Contract with ID {contract_id_int} not found")
        
        db.commit()
        print(f"Successfully deleted contract {contract_id_int}")
        
        return {
            "message": "Contract deleted successfully",
            "deleted_analysis": analysis_deleted,
            "deleted_rewrite": rewrite_deleted,
            "deleted_generation": generation_deleted
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid contract ID format")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting contract: {str(e)}")

@router.get("/history/{contract_id}")
async def get_contract_by_id(
    contract_id: str,
    db: Session = Depends(get_db)
) -> ContractHistoryResponse:
    """
    Get a specific contract from history by ID.
    """
    try:
        contract_id_int = int(contract_id)
          # Look in analysis table first
        analysis_entry = db.query(ContractAnalysisDB).filter(ContractAnalysisDB.id == contract_id_int).first()
        if analysis_entry:
            return ContractHistoryResponse(
                id=str(analysis_entry.id),
                type="analysis",
                contract_name=analysis_entry.contract_name,
                timestamp=analysis_entry.requested_at,
                success=analysis_entry.analysis_report is not None,
                details={"analysis_report": analysis_entry.analysis_report}
            )
          # Look in rewrite table
        rewrite_entry = db.query(ContractRewriteDB).filter(ContractRewriteDB.id == contract_id_int).first()
        if rewrite_entry:
            return ContractHistoryResponse(
                id=str(rewrite_entry.id),
                type="rewrite",
                contract_name=rewrite_entry.contract_name,
                timestamp=rewrite_entry.requested_at,
                success=rewrite_entry.rewritten_code is not None,
                optimization_goals=rewrite_entry.optimization_goals,
                details={"rewrite_summary": rewrite_entry.rewrite_summary}
            )
        
        # Look in generation table
        generation_entry = db.query(ContractGenerationDB).filter(ContractGenerationDB.id == contract_id_int).first()
        if generation_entry:
            return ContractHistoryResponse(
                id=str(generation_entry.id),
                type="generation",
                contract_name=generation_entry.contract_name,
                timestamp=generation_entry.requested_at,
                success=generation_entry.generated_code is not None and generation_entry.completed_at is not None,
                details={
                    "generated_code": generation_entry.generated_code,
                    "description": generation_entry.description,
                    "features": generation_entry.features,
                    "generation_metadata": generation_entry.generation_metadata
                }
            )
        
        raise HTTPException(status_code=404, detail="Contract not found")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid contract ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving contract: {str(e)}")

@router.post("/generate", response_model=ContractOutput)
async def generate_contract(
    generation_request: dict = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate a smart contract based on user description using Gemini AI.
    """
    try:
        description = generation_request.get("description", "")
        contract_name = generation_request.get("contract_name", "GeneratedContract")
        features = generation_request.get("features", [])
        solidity_version = generation_request.get("compiler_version", "0.8.19")
        
        if not description:
            raise HTTPException(status_code=400, detail="Contract description is required")
        
        # Generate contract using Gemini AI
        generation_result = await contract_service.generate_contract(
            description=description,
            contract_name=contract_name,
            features=features,
            solidity_version=solidity_version
        )
        
        # Log the generation to the database in the background
        background_tasks.add_task(
            log_generation_to_db,
            db=db,
            generation_request=generation_request,
            generation_result=generation_result,
            success=True
        )
        
        return generation_result
        
    except Exception as e:
        background_tasks.add_task(
            log_generation_to_db,
            db=db,
            generation_request=generation_request,
            generation_result=None,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error generating contract: {str(e)}")
