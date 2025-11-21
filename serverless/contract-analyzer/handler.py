"""
AWS Lambda Handler for Smart Contract Analysis
Uses OpenAI (primary) and Google Gemini (fallback) for AI-powered analysis

This Lambda function is triggered by API Gateway and analyzes Solidity smart contracts
for security vulnerabilities, gas optimization opportunities, and best practices.
"""

import json
import os
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

# AI Service imports
try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Environment Variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

# Initialize AI services
openai_client = None
gemini_model = None

if OPENAI_API_KEY and openai:
    openai.api_key = OPENAI_API_KEY
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI initialized")

if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        print("✅ Gemini initialized as fallback")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini: {e}")


class ContractAnalyzer:
    """
    Smart Contract Analyzer using AI services
    
    This class handles the analysis logic with automatic fallback:
    1. Try OpenAI first (faster, more accurate)
    2. Fall back to Gemini if OpenAI fails
    3. Return detailed vulnerability and gas optimization reports
    """
    
    def __init__(self):
        self.openai_available = openai_client is not None
        self.gemini_available = gemini_model is not None
        
        if not self.openai_available and not self.gemini_available:
            print("⚠️ WARNING: No AI services available!")
    
    def create_analysis_prompt(self, contract_code: str, analysis_type: str = "security") -> str:
        """
        Create a specialized prompt for contract analysis
        
        Args:
            contract_code: The Solidity contract code to analyze
            analysis_type: Type of analysis (security, gas, general)
        
        Returns:
            Formatted prompt string for AI model
        """
        
        if analysis_type == "security":
            return f"""
Perform a comprehensive security audit of this Solidity smart contract:

{contract_code}

Analyze for:
1. Reentrancy vulnerabilities
2. Access control issues
3. Integer overflow/underflow
4. Unchecked external calls
5. Front-running risks
6. Timestamp dependence
7. DoS vulnerabilities
8. Logic errors

Return a JSON response with:
{{
    "vulnerabilities": [
        {{
            "type": "vulnerability_type",
            "severity": "critical|high|medium|low",
            "line_number": line_number,
            "description": "detailed description",
            "recommendation": "how to fix"
        }}
    ],
    "overall_security_score": 0-100,
    "general_suggestions": ["suggestion1", "suggestion2"]
}}
"""
        
        elif analysis_type == "gas":
            return f"""
Analyze this Solidity contract for gas optimization opportunities:

{contract_code}

Identify:
1. Expensive storage operations
2. Redundant computations
3. Loop optimizations
4. Variable packing opportunities
5. Memory vs storage usage
6. Function visibility optimization
7. Event emission costs

Return a JSON response with:
{{
    "gas_analysis_per_function": [
        {{
            "function_name": "function_name",
            "estimated_gas": gas_amount,
            "optimization_potential": "high|medium|low",
            "suggestions": ["suggestion1", "suggestion2"]
        }}
    ],
    "total_deployment_gas": estimated_amount,
    "optimization_priority": ["priority1", "priority2"]
}}
"""
        
        else:  # general analysis
            return f"""
Perform a comprehensive analysis of this Solidity smart contract:

{contract_code}

Include:
1. Code quality assessment
2. Best practices compliance
3. Design patterns used
4. Potential improvements
5. Security considerations
6. Gas efficiency

Return a JSON response with detailed findings.
"""
    
    async def analyze_with_openai(self, contract_code: str, analysis_type: str) -> Dict[str, Any]:
        """
        Analyze contract using OpenAI GPT-4
        
        OpenAI is preferred because:
        - Better code understanding
        - More consistent JSON responses
        - Faster response times
        - Better at identifying subtle security issues
        """
        
        prompt = self.create_analysis_prompt(contract_code, analysis_type)
        start_time = time.time()
        
        try:
            # Use asyncio.to_thread to make sync OpenAI call async
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert Solidity smart contract security auditor. Return responses in valid JSON format."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent, factual responses
                max_tokens=4000,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            processing_time = time.time() - start_time
            content = response.choices[0].message.content
            
            # Parse the JSON response
            result = json.loads(content)
            result["processing_time"] = processing_time
            result["model_used"] = OPENAI_MODEL
            result["service_used"] = "OpenAI"
            
            print(f"✅ OpenAI analysis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            print(f"❌ OpenAI analysis failed: {str(e)}")
            raise
    
    async def analyze_with_gemini(self, contract_code: str, analysis_type: str) -> Dict[str, Any]:
        """
        Analyze contract using Google Gemini (fallback)
        
        Gemini is used as fallback when:
        - OpenAI is unavailable
        - OpenAI rate limits exceeded
        - Cost optimization needed (Gemini is cheaper)
        """
        
        prompt = self.create_analysis_prompt(contract_code, analysis_type)
        start_time = time.time()
        
        try:
            # Gemini's generate_content is synchronous, wrap in asyncio
            response = await asyncio.to_thread(
                gemini_model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 4000,
                }
            )
            
            processing_time = time.time() - start_time
            content = response.text
            
            # Try to extract JSON from response
            # Gemini sometimes wraps JSON in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            result["processing_time"] = processing_time
            result["model_used"] = GEMINI_MODEL
            result["service_used"] = "Gemini"
            
            print(f"✅ Gemini analysis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            print(f"❌ Gemini analysis failed: {str(e)}")
            raise
    
    async def analyze(self, contract_code: str, analysis_type: str = "security") -> Dict[str, Any]:
        """
        Main analysis method with automatic fallback
        
        Flow:
        1. Try OpenAI (primary)
        2. If OpenAI fails, try Gemini (fallback)
        3. If both fail, return error
        
        Args:
            contract_code: Solidity contract code
            analysis_type: Type of analysis to perform
        
        Returns:
            Analysis results dictionary
        """
        
        # Try OpenAI first
        if self.openai_available:
            try:
                return await self.analyze_with_openai(contract_code, analysis_type)
            except Exception as e:
                print(f"⚠️ OpenAI failed, trying Gemini fallback: {e}")
        
        # Fallback to Gemini
        if self.gemini_available:
            try:
                return await self.analyze_with_gemini(contract_code, analysis_type)
            except Exception as e:
                print(f"❌ Gemini also failed: {e}")
                raise Exception("All AI services unavailable")
        
        raise Exception("No AI services configured")


# Initialize the analyzer (reused across Lambda invocations - Lambda container reuse)
analyzer = ContractAnalyzer()


def lambda_handler(event, context):
    """
    AWS Lambda Handler Function
    
    This is the entry point for the Lambda function. AWS invokes this when:
    - API Gateway receives a request
    - S3 upload triggers the function
    - EventBridge scheduled event fires
    
    Args:
        event: AWS Lambda event object (contains request data)
        context: AWS Lambda context object (runtime info)
    
    Returns:
        Response object with statusCode, headers, and body
    """
    
    print(f"📥 Lambda invoked at {datetime.utcnow().isoformat()}")
    print(f"Request ID: {context.request_id}")
    print(f"Memory limit: {context.memory_limit_in_mb}MB")
    
    try:
        # Parse the incoming request
        # For API Gateway, body is a JSON string
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract contract code and analysis type
        contract_code = body.get('contract_code')
        contract_name = body.get('contract_name', 'Unknown')
        analysis_type = body.get('analysis_type', 'security')
        
        # Validation
        if not contract_code:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    'error': 'contract_code is required',
                    'message': 'Please provide Solidity contract code to analyze'
                })
            }
        
        # Basic contract validation
        if 'contract' not in contract_code.lower() and 'pragma' not in contract_code.lower():
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'invalid_contract',
                    'message': 'Provided code does not appear to be a valid Solidity contract'
                })
            }
        
        print(f"🔍 Analyzing contract: {contract_name}")
        print(f"Analysis type: {analysis_type}")
        print(f"Contract size: {len(contract_code)} characters")
        
        # Perform analysis (async operation)
        # Lambda supports asyncio by running it in the event loop
        loop = asyncio.get_event_loop()
        analysis_result = loop.run_until_complete(
            analyzer.analyze(contract_code, analysis_type)
        )
        
        # Format response for frontend
        response_body = {
            'request_id': context.request_id,
            'contract_name': contract_name,
            'analysis_type': analysis_type,
            'analysis_report': analysis_result,
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Contract analysis completed successfully'
        }
        
        print(f"✅ Analysis completed successfully")
        print(f"Service used: {analysis_result.get('service_used')}")
        print(f"Processing time: {analysis_result.get('processing_time', 0):.2f}s")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps(response_body)
        }
    
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'analysis_failed',
                'message': str(e),
                'request_id': context.request_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def handler_for_s3_trigger(event, context):
    """
    Alternative handler for S3-triggered Lambda
    
    This handles automatic analysis when a .sol file is uploaded to S3:
    1. S3 upload triggers Lambda
    2. Lambda reads the file from S3
    3. Analyzes the contract
    4. Stores results back to S3 or DynamoDB
    
    Use case: Batch processing of contracts
    """
    
    print("📦 S3 trigger received")
    
    try:
        import boto3
        s3_client = boto3.client('s3')
        
        # Get bucket and key from S3 event
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Processing file: s3://{bucket}/{key}")
            
            # Download file from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            contract_code = response['Body'].read().decode('utf-8')
            
            # Extract contract name from filename
            contract_name = key.split('/')[-1].replace('.sol', '')
            
            # Analyze the contract
            loop = asyncio.get_event_loop()
            analysis_result = loop.run_until_complete(
                analyzer.analyze(contract_code, "security")
            )
            
            # Store results back to S3
            result_key = key.replace('.sol', '_analysis.json')
            s3_client.put_object(
                Bucket=bucket,
                Key=result_key,
                Body=json.dumps(analysis_result, indent=2),
                ContentType='application/json'
            )
            
            print(f"✅ Results stored to: s3://{bucket}/{result_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Analysis completed and results stored'})
        }
    
    except Exception as e:
        print(f"❌ S3 handler error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
