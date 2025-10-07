"""
AI Service Microservice
Handles all AI/ML operations with OpenAI as primary and Gemini as fallback
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import openai
import json
import os
import time
import asyncio
from datetime import datetime

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Configure AI services
openai_client = None
gemini_model = None

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
    except Exception as e:
        print(f"Failed to initialize Gemini model: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="SoliVolt AI Service",
    description="AI/ML microservice for smart contract analysis and generation with OpenAI primary, Gemini fallback",
    version="2.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ContractAnalysisRequest(BaseModel):
    contract_code: str
    contract_name: Optional[str] = None
    analysis_type: str = "security"  # security, gas, general
    user_id: Optional[int] = None

class ContractGenerationRequest(BaseModel):
    description: str
    features: List[str] = []
    contract_type: str = "erc20"  # erc20, erc721, custom
    user_id: Optional[int] = None

class AIResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    model_used: str
    timestamp: str

class EnhancedAIService:
    """Enhanced AI Service with OpenAI primary and Gemini fallback"""
    
    def __init__(self):
        self.openai_available = openai_client is not None
        self.gemini_available = gemini_model is not None
        
        if not self.openai_available and not self.gemini_available:
            print("Warning: No AI services available!")
    
    async def analyze_contract(self, contract_code: str, analysis_type: str = "security") -> Dict[str, Any]:
        """Analyze smart contract using OpenAI first, then Gemini as fallback"""
        
        # Try OpenAI first
        if self.openai_available:
            try:
                return await self._analyze_with_openai(contract_code, analysis_type)
            except Exception as e:
                print(f"OpenAI analysis failed, falling back to Gemini: {e}")
        
        # Fallback to Gemini
        if self.gemini_available:
            try:
                return await self._analyze_with_gemini(contract_code, analysis_type)
            except Exception as e:
                print(f"Gemini analysis also failed: {e}")
                raise HTTPException(status_code=503, detail="All AI services unavailable")
        
        raise HTTPException(status_code=503, detail="No AI services available")
    
    async def generate_contract(self, description: str, features: List[str], contract_type: str) -> Dict[str, Any]:
        """Generate smart contract using OpenAI first, then Gemini as fallback"""
        
        # Try OpenAI first
        if self.openai_available:
            try:
                return await self._generate_with_openai(description, features, contract_type)
            except Exception as e:
                print(f"OpenAI generation failed, falling back to Gemini: {e}")
        
        # Fallback to Gemini
        if self.gemini_available:
            try:
                return await self._generate_with_gemini(description, features, contract_type)
            except Exception as e:
                print(f"Gemini generation also failed: {e}")
                raise HTTPException(status_code=503, detail="All AI services unavailable")
        
        raise HTTPException(status_code=503, detail="No AI services available")
    
    async def _analyze_with_openai(self, contract_code: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze contract using OpenAI"""
        prompt = self._create_analysis_prompt(contract_code, analysis_type)
        
        start_time = time.time()
        
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert Solidity smart contract security auditor and gas optimization specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        processing_time = time.time() - start_time
        content = response.choices[0].message.content
        
        result = self._parse_analysis_response(content, analysis_type)
        result["processing_time"] = processing_time
        result["model_used"] = OPENAI_MODEL
        result["service_used"] = "OpenAI"
        
        return result
    
    async def _generate_with_openai(self, description: str, features: List[str], contract_type: str) -> Dict[str, Any]:
        """Generate contract using OpenAI"""
        prompt = self._create_generation_prompt(description, features, contract_type)
        
        start_time = time.time()
        
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert Solidity developer specializing in secure smart contract development."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        processing_time = time.time() - start_time
        content = response.choices[0].message.content
        
        result = self._parse_generation_response(content)
        result["processing_time"] = processing_time
        result["model_used"] = OPENAI_MODEL
        result["service_used"] = "OpenAI"
        
        return result
    
    async def _analyze_with_gemini(self, contract_code: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze contract using Gemini (fallback)"""
        prompt = self._create_analysis_prompt(contract_code, analysis_type)
        
        start_time = time.time()
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        processing_time = time.time() - start_time
        
        result = self._parse_analysis_response(response.text, analysis_type)
        result["processing_time"] = processing_time
        result["model_used"] = GEMINI_MODEL
        result["service_used"] = "Gemini"
        
        return result
    
    async def _generate_with_gemini(self, description: str, features: List[str], contract_type: str) -> Dict[str, Any]:
        """Generate contract using Gemini (fallback)"""
        prompt = self._create_generation_prompt(description, features, contract_type)
        
        start_time = time.time()
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        processing_time = time.time() - start_time
        
        result = self._parse_generation_response(response.text)
        result["processing_time"] = processing_time
        result["model_used"] = GEMINI_MODEL
        result["service_used"] = "Gemini"
        
        return result
    
    def _create_analysis_prompt(self, contract_code: str, analysis_type: str) -> str:
        """Create analysis prompt based on type"""
        if analysis_type == "security":
            return f"""
            You are an expert smart contract security auditor. Analyze the following Solidity contract for security vulnerabilities, gas optimization opportunities, and best practices.

            Contract Code:
            ```solidity
            {contract_code}
            ```

            Please provide a detailed analysis in the following JSON format:
            {{
                "vulnerabilities": [
                    {{
                        "type": "vulnerability_name",
                        "severity": "High|Medium|Low",
                        "line_number": 0,
                        "description": "detailed description",
                        "recommendation": "how to fix"
                    }}
                ],
                "gas_optimizations": [
                    {{
                        "function_name": "function_name",
                        "issue": "description of gas issue",
                        "recommendation": "optimization suggestion",
                        "estimated_savings": "percentage or amount"
                    }}
                ],
                "code_quality": {{
                    "score": 85,
                    "issues": ["list of code quality issues"],
                    "suggestions": ["list of improvements"]
                }},
                "summary": "Overall assessment and key recommendations"
            }}

            Focus on common vulnerabilities like reentrancy, integer overflow/underflow, access control issues, and gas optimization opportunities.
            """
        elif analysis_type == "gas":
            return f"""
            You are a Solidity gas optimization expert. Analyze the following contract for gas efficiency improvements.

            Contract Code:
            ```solidity
            {contract_code}
            ```

            Please provide gas optimization analysis in JSON format:
            {{
                "gas_analysis_per_function": [
                    {{
                        "function_name": "function_name",
                        "current_complexity": "estimated gas usage",
                        "optimizations": ["list of optimization suggestions"],
                        "potential_savings": "estimated percentage savings"
                    }}
                ],
                "general_optimizations": [
                    "storage optimization suggestions",
                    "computation optimization suggestions"
                ],
                "estimated_total_savings": "overall percentage savings"
            }}
            """
        else:
            return f"""
            Provide a comprehensive analysis of this Solidity smart contract:

            ```solidity
            {contract_code}
            ```

            Include security, gas efficiency, code quality, and functionality assessment in JSON format.
            """
    
    def _create_generation_prompt(self, description: str, features: List[str], contract_type: str) -> str:
        """Create contract generation prompt"""
        features_str = ", ".join(features) if features else "basic functionality"
        
        return f"""
        Generate a secure and well-documented Solidity smart contract based on the following requirements:

        Description: {description}
        Contract Type: {contract_type}
        Required Features: {features_str}

        Please provide the response in the following JSON format:
        {{
            "generated_code": "complete Solidity contract code",
            "explanation": "explanation of the contract functionality",
            "security_considerations": ["list of security features implemented"],
            "usage_instructions": "how to deploy and use the contract",
            "test_suggestions": ["list of tests that should be written"]
        }}

        Ensure the contract follows best practices, includes proper error handling, and has comprehensive documentation.
        """
    
    def _parse_analysis_response(self, response_text: str, analysis_type: str) -> Dict[str, Any]:
        """Parse AI analysis response"""
        try:
            # Try to extract JSON from the response
            start_json = response_text.find('{')
            end_json = response_text.rfind('}') + 1
            
            if start_json != -1 and end_json != -1:
                json_str = response_text[start_json:end_json]
                return json.loads(json_str)
            else:
                # Fallback to text response
                return {
                    "analysis_type": analysis_type,
                    "raw_response": response_text,
                    "parsed": False
                }
        except json.JSONDecodeError:
            return {
                "analysis_type": analysis_type,
                "raw_response": response_text,
                "parsed": False
            }
    
    def _parse_generation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI generation response"""
        try:
            # Try to extract JSON from the response
            start_json = response_text.find('{')
            end_json = response_text.rfind('}') + 1
            
            if start_json != -1 and end_json != -1:
                json_str = response_text[start_json:end_json]
                return json.loads(json_str)
            else:
                # Fallback: extract Solidity code if present
                solidity_start = response_text.find('```solidity')
                solidity_end = response_text.find('```', solidity_start + 1)
                
                if solidity_start != -1 and solidity_end != -1:
                    code = response_text[solidity_start + 11:solidity_end].strip()
                    return {
                        "generated_code": code,
                        "explanation": "Generated smart contract",
                        "raw_response": response_text
                    }
                else:
                    return {
                        "generated_code": response_text,
                        "explanation": "Raw generated content",
                        "raw_response": response_text
                    }
        except json.JSONDecodeError:
            return {
                "generated_code": response_text,
                "explanation": "Generated content (unparsed)",
                    "raw_response": response_text
                }

# Initialize AI service
ai_service = EnhancedAIService()# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "2.0.0",
        "ai_services": {
            "openai": {
                "available": ai_service.openai_available,
                "model": OPENAI_MODEL if ai_service.openai_available else None,
                "priority": "primary"
            },
            "gemini": {
                "available": ai_service.gemini_available,
                "model": GEMINI_MODEL if ai_service.gemini_available else None,
                "priority": "fallback"
            }
        },
        "strategy": "OpenAI primary, Gemini fallback"
    }

@app.post("/api/v1/ai/analyze", response_model=AIResponse)
async def analyze_contract(request: ContractAnalysisRequest):
    """Analyze smart contract using AI"""
    start_time = time.time()
    
    try:
        result = await ai_service.analyze_contract(
            request.contract_code, 
            request.analysis_type
        )
        
        processing_time = time.time() - start_time
        
        return AIResponse(
            success=True,
            data=result,
            processing_time=processing_time,
            model_used=GEMINI_MODEL,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        return AIResponse(
            success=False,
            data={"error": str(e)},
            processing_time=processing_time,
            model_used=GEMINI_MODEL,
            timestamp=datetime.now().isoformat()
        )

@app.post("/api/v1/ai/generate", response_model=AIResponse)
async def generate_contract(request: ContractGenerationRequest):
    """Generate smart contract using AI"""
    start_time = time.time()
    
    try:
        result = await ai_service.generate_contract(
            request.description,
            request.features,
            request.contract_type
        )
        
        processing_time = time.time() - start_time
        
        return AIResponse(
            success=True,
            data=result,
            processing_time=processing_time,
            model_used=GEMINI_MODEL,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        return AIResponse(
            success=False,
            data={"error": str(e)},
            processing_time=processing_time,
            model_used=GEMINI_MODEL,
            timestamp=datetime.now().isoformat()
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SoliVolt AI Service",
        "version": "2.0.0",
        "endpoints": {
            "analyze": "/api/v1/ai/analyze",
            "generate": "/api/v1/ai/generate",
            "health": "/health",
            "docs": "/docs"
        },
        "ai_strategy": "OpenAI primary, Gemini fallback",
        "models": {
            "openai": OPENAI_MODEL,
            "gemini": GEMINI_MODEL
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
