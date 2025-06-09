from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

from app.models.contract_models import OptimizationGoal, VulnerabilityType # Assuming Pydantic enums can be used

Base = declarative_base()

class User(Base): # Optional: If you plan to add user accounts
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True) # Nullable if using external auth
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    analyses = relationship("ContractAnalysisDB", back_populates="user")
    rewrites = relationship("ContractRewriteDB", back_populates="user")

class ContractAnalysisDB(Base):
    __tablename__ = "contract_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional user link
    
    contract_name = Column(String(255), index=True, nullable=True)
    original_code = Column(Text, nullable=False)
    
    # Store Pydantic models as JSON
    analysis_report = Column(JSON, nullable=False) # Stores AnalysisReport Pydantic model
    vulnerabilities_found = Column(JSON, nullable=True) # Stores list of VulnerabilityInfo
    gas_analysis = Column(JSON, nullable=True) # Stores GasAnalysis Pydantic model
    
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    rewrite_entries = relationship("ContractRewriteDB", back_populates="analysis_entry")


class ContractRewriteDB(Base):
    __tablename__ = "contract_rewrites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional user link
    analysis_id = Column(Integer, ForeignKey("contract_analyses.id"), nullable=True) # Link to an analysis

    contract_name = Column(String(255), index=True, nullable=True)
    original_code = Column(Text, nullable=False) # Can be derived from analysis_id or stored
    rewritten_code = Column(Text, nullable=False)
    
    # Using ARRAY of strings for optimization goals, assuming OptimizationGoal enum values are strings
    optimization_goals = Column(ARRAY(String), nullable=True)
    
    # Store Pydantic models as JSON
    rewrite_summary = Column(JSON, nullable=True) # Could store a summary of changes or performance improvements
    
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="rewrites")
    analysis_entry = relationship("ContractAnalysisDB", back_populates="rewrite_entries")

# Example of how you might store raw Gemini API call/response if needed for auditing or debugging
class GeminiAPILogDB(Base):
    __tablename__ = "gemini_api_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_payload = Column(JSON, nullable=False)
    response_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    called_at = Column(DateTime(timezone=True), server_default=func.now())
    duration_ms = Column(Integer, nullable=True)
    related_analysis_id = Column(Integer, ForeignKey("contract_analyses.id"), nullable=True)
    related_rewrite_id = Column(Integer, ForeignKey("contract_rewrites.id"), nullable=True)

# You might also want a table for storing contract source codes if they are reused or versioned
# class SmartContractSourceDB(Base):
#     __tablename__ = "smart_contract_sources"
#     id = Column(Integer, primary_key=True, index=True)
#     code_hash = Column(String(64), unique=True, index=True) # SHA256 hash of the code
#     source_code = Column(Text, nullable=False)
#     language = Column(String(50), default="Solidity") # e.g., Solidity, Vyper
#     compiler_version = Column(String(50), nullable=True)
#     first_seen_at = Column(DateTime(timezone=True), server_default=func.now())

