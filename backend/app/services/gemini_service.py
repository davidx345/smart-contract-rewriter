import google.generativeai as genai
from app.core.config import settings
import json
import re
from typing import Dict, Any
import asyncio


class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    async def analyze_contract(self, contract_code: str, contract_name: str) -> Dict[str, Any]:
        """Analyze smart contract for vulnerabilities and issues"""
        
        prompt = f"""
You are an expert smart contract auditor with deep knowledge of Solidity security patterns and gas optimization. 
Analyze the following Solidity smart contract thoroughly.

Contract Name: {contract_name or "Unknown"}
Contract Code:
```solidity
{contract_code}
```

Provide a comprehensive analysis in VALID JSON format only (no markdown, no extra text):
{{
    "vulnerabilities": [
        {{
            "type": "reentrancy|integer_overflow|access_control|unhandled_exceptions|front_running|timestamp_dependence|gas_limit_issues|denial_of_service|logic_errors|short_address_attack",
            "severity": "Low|Medium|High|Critical",
            "line_number": null_or_line_number,
            "description": "Clear description of the vulnerability",
            "recommendation": "Specific fix recommendation"
        }}
    ],
    "gas_analysis_per_function": [
        {{
            "function_name": "function_name",
            "original_gas": estimated_gas_cost_number,
            "optimization_opportunities": ["specific gas optimization suggestions"]
        }}
    ],
    "overall_code_quality_score": number_between_0_and_10,
    "overall_security_score": number_between_0_and_10,
    "general_suggestions": [
        "Actionable improvement suggestions"
    ],
    "confidence_score": number_between_0_and_1
}}

Focus on:
- Common attack vectors (reentrancy, overflow, access control)
- Gas optimization opportunities
- Code quality and best practices
- Security vulnerabilities specific to DeFi/smart contracts
"""
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return self._parse_analysis_response(response.text)
        except Exception as e:
            print(f"Error in Gemini analysis: {e}")
            return self._default_analysis_response()
    
    async def rewrite_contract(self, contract_code: str, contract_name: str, optimization_goals: list) -> Dict[str, Any]:
        """Rewrite and optimize smart contract based on goals"""
        
        goals_str = ", ".join(optimization_goals)
        
        prompt = f"""
You are an expert Solidity developer and smart contract optimizer. 
Rewrite and optimize the following smart contract based on these specific goals: {goals_str}

Contract Name: {contract_name or "Unknown"}
Original Contract:
```solidity
{contract_code}
```

Optimization Goals: {goals_str}

Provide your response in VALID JSON format only (no markdown, no extra text):
{{
    "rewritten_code": "// Complete rewritten Solidity code here - ensure it's valid Solidity",
    "changes_summary": [
        "Brief description of major changes made"
    ],
    "security_enhancements_made": [
        "Specific security improvements implemented"
    ],
    "readability_notes": "Optional notes about code readability improvements",
    "analysis_of_rewritten_code": {{
        "vulnerabilities": [],
        "gas_analysis_per_function": [
            {{
                "function_name": "function_name",
                "original_gas": original_estimate,
                "optimized_gas": optimized_estimate,
                "savings_percentage": percentage_improvement
            }}
        ],
        "overall_code_quality_score": improved_score_0_to_10,
        "overall_security_score": improved_score_0_to_10,
        "general_suggestions": ["any remaining suggestions"]
    }},
    "confidence_score": number_between_0_and_1,
    "diff_summary": "Brief textual summary of key changes"
}}

Requirements:
- Preserve all original functionality unless explicitly optimizing it
- Focus on the specified optimization goals
- Ensure the rewritten code compiles and is secure
- Provide measurable improvements where possible
- Use latest Solidity patterns (0.8.x+)
- Add proper error handling and events
- Include comprehensive comments
"""
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return self._parse_rewrite_response(response.text)
        except Exception as e:
            print(f"Error in Gemini rewrite: {e}")
            return self._default_rewrite_response(contract_code)
    
    async def generate_contract(self, description: str, contract_name: str, features: list = None) -> Dict[str, Any]:
        """Generate a smart contract from user description"""
        
        features_text = ""
        if features:
            features_text = f"\nAdditional Features: {', '.join(features)}"
        
        prompt = f"""
You are an expert Solidity smart contract developer. Generate a complete, secure, and well-documented smart contract based on the user's description.

Contract Name: {contract_name}
User Description: {description}{features_text}

Requirements:
- Use Solidity version 0.8.19 or higher
- Include proper security measures (access control, reentrancy protection, etc.)
- Add comprehensive comments and documentation
- Follow best practices for gas optimization
- Include relevant events and error handling
- Make the contract production-ready

Provide your response in VALID JSON format only (no markdown, no extra text):
{{
    "contract_code": "// Complete Solidity contract code here\n// SPDX-License-Identifier: MIT\npragma solidity ^0.8.19;\n\n// Your contract implementation",
    "generation_notes": "Brief explanation of the generated contract and its features",
    "contract_features": [
        "List of key features implemented"
    ],
    "security_measures": [
        "List of security measures included"
    ],
    "usage_instructions": "How to deploy and use this contract",
    "potential_improvements": [
        "Suggestions for future enhancements"
    ],
    "confidence_score": number_between_0_and_1
}}

Focus on:
- Implementing exactly what the user described
- Adding proper security measures
- Writing clean, well-commented code
- Following Solidity best practices
- Making the contract gas-efficient
- Including proper error handling
"""
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return self._parse_generation_response(response.text)
        except Exception as e:
            print(f"Error in Gemini contract generation: {e}")
            return self._default_generation_response()

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's analysis response"""
        try:
            # Clean the response to extract JSON
            cleaned_response = self._clean_json_response(response_text)
            parsed = json.loads(cleaned_response)
            
            # Validate required fields
            if not isinstance(parsed.get("vulnerabilities"), list):
                parsed["vulnerabilities"] = []
            if not isinstance(parsed.get("gas_analysis_per_function"), list):
                parsed["gas_analysis_per_function"] = []
            if not isinstance(parsed.get("general_suggestions"), list):
                parsed["general_suggestions"] = []
            
            return parsed
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Gemini analysis response: {e}")
            return self._default_analysis_response()
    
    def _parse_rewrite_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's rewrite response"""
        try:
            # Clean the response to extract JSON
            cleaned_response = self._clean_json_response(response_text)
            parsed = json.loads(cleaned_response)
            
            # Validate required fields
            if not parsed.get("rewritten_code"):
                parsed["rewritten_code"] = "// Error: No rewritten code provided"
            if not isinstance(parsed.get("changes_summary"), list):
                parsed["changes_summary"] = []
            if not isinstance(parsed.get("security_enhancements_made"), list):
                parsed["security_enhancements_made"] = []
            
            return parsed
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Gemini rewrite response: {e}")
            return self._default_rewrite_response("// Error in rewrite process")
    
    def _parse_generation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's contract generation response"""
        try:
            # Clean the response to extract JSON
            cleaned_response = self._clean_json_response(response_text)
            parsed = json.loads(cleaned_response)
            
            # Validate required fields
            if not parsed.get("contract_code"):
                parsed["contract_code"] = f"// Error: Contract generation failed\n// SPDX-License-Identifier: MIT\npragma solidity ^0.8.19;\n\ncontract ErrorContract {{\n    // Generation failed\n}}"
            if not isinstance(parsed.get("contract_features"), list):
                parsed["contract_features"] = []
            if not isinstance(parsed.get("security_measures"), list):
                parsed["security_measures"] = []
            
            return parsed
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Gemini generation response: {e}")
            return self._default_generation_response()

    def _clean_json_response(self, response_text: str) -> str:
        """Clean response text to extract valid JSON"""
        # Remove markdown code blocks
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*$', '', response_text)
        
        # Find JSON object boundaries
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            return response_text[start_idx:end_idx+1]
        
        return response_text.strip()
    
    def _default_analysis_response(self) -> Dict[str, Any]:
        """Default response when analysis fails"""
        return {
            "vulnerabilities": [],
            "gas_analysis_per_function": [],
            "overall_code_quality_score": 5.0,
            "overall_security_score": 5.0,
            "general_suggestions": ["Analysis could not be completed. Please check contract syntax."],
            "confidence_score": 0.0
        }
    
    def _default_rewrite_response(self, original_code: str) -> Dict[str, Any]:
        """Default response when rewrite fails"""
        return {
            "rewritten_code": original_code,
            "changes_summary": ["No changes made due to processing error"],
            "security_enhancements_made": [],
            "readability_notes": "Rewrite process encountered an error",
            "analysis_of_rewritten_code": {
                "vulnerabilities": [],
                "gas_analysis_per_function": [],
                "overall_code_quality_score": 5.0,
                "overall_security_score": 5.0,
                "general_suggestions": []
            },
            "confidence_score": 0.0,
            "diff_summary": "No changes applied"
        }

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response for analysis"""
        try:
            # Remove code blocks and extract JSON
            cleaned_text = response_text.strip()
            if "```json" in cleaned_text:
                json_start = cleaned_text.find("```json") + 7
                json_end = cleaned_text.find("```", json_start)
                cleaned_text = cleaned_text[json_start:json_end].strip()
            elif "```" in cleaned_text:
                json_start = cleaned_text.find("```") + 3
                json_end = cleaned_text.find("```", json_start)
                cleaned_text = cleaned_text[json_start:json_end].strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group())
                # Validate required fields
                if "vulnerabilities" in parsed_json and "general_suggestions" in parsed_json:
                    return parsed_json
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
        except Exception as e:
            print(f"Response parsing error: {e}")
        
        return self._default_analysis_response()
    
    def _parse_rewrite_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response for rewrite"""
        try:
            # Remove code blocks and extract JSON
            cleaned_text = response_text.strip()
            if "```json" in cleaned_text:
                json_start = cleaned_text.find("```json") + 7
                json_end = cleaned_text.find("```", json_start)
                cleaned_text = cleaned_text[json_start:json_end].strip()
            elif "```" in cleaned_text:
                json_start = cleaned_text.find("```") + 3
                json_end = cleaned_text.find("```", json_start)
                cleaned_text = cleaned_text[json_start:json_end].strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group())
                # Validate required fields
                if "rewritten_code" in parsed_json:
                    return parsed_json
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
        except Exception as e:
            print(f"Response parsing error: {e}")
        
        return self._default_rewrite_response("")
    
    def _default_analysis_response(self) -> Dict[str, Any]:
        """Default response when analysis fails"""
        return {
            "vulnerabilities": [],
            "gas_analysis_per_function": [],
            "overall_code_quality_score": 5.0,
            "overall_security_score": 5.0,
            "general_suggestions": ["Analysis service temporarily unavailable. Please try again."],
            "confidence_score": 0.0
        }
    
    def _default_rewrite_response(self, original_code: str) -> Dict[str, Any]:
        """Default response when rewrite fails"""
        return {
            "rewritten_code": original_code,
            "changes_summary": ["Rewrite service temporarily unavailable"],
            "security_enhancements_made": [],
            "readability_notes": "No changes applied",
            "diff_summary": "No changes made due to service error",
            "confidence_score": 0.0,
            "analysis_of_rewritten_code": {
                "vulnerabilities": [],
                "gas_analysis_per_function": [],
                "overall_code_quality_score": 5.0,
                "overall_security_score": 5.0,
                "general_suggestions": []
            }
        }
