import time
import asyncio
import uuid  # Added for request_id
from app.models.contract_models import (
    ContractInput,
    ContractOutput,
    OptimizationRequest,
    AnalysisReport,
    RewriteReport,  # Added
    VulnerabilityInfo,
    GasFunctionAnalysis,  # Renamed from GasAnalysis
    VulnerabilityType,
    OptimizationGoal  # Added for typing if needed
)
from app.services.gemini_service import GeminiService
from app.services.web3_service import Web3Service


class ContractProcessingService:
    def __init__(self):
        self.gemini_service = GeminiService()
        self.web3_service = Web3Service()

    async def process_contract_analysis(self, contract_input: ContractInput) -> ContractOutput:
        """Analyze a smart contract using Gemini AI and Web3"""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Get analysis from Gemini
            # Assuming gemini_service.analyze_contract now takes source_code
            analysis_data = await self.gemini_service.analyze_contract(
                contract_input.source_code,
                contract_input.contract_name
            )

            vulnerabilities = []
            if analysis_data.get("vulnerabilities"):
                for vuln_data in analysis_data.get("vulnerabilities", []):
                    try:
                        # Ensure VulnerabilityType enum conversion is robust
                        vuln_type_str = vuln_data.get("type")
                        vuln_type = VulnerabilityType(vuln_type_str) if vuln_type_str in VulnerabilityType.__members__ else VulnerabilityType.LOGIC_ERRORS  # Default or handle error
                        vuln = VulnerabilityInfo(
                            type=vuln_type,
                            severity=vuln_data.get("severity", "Medium"),
                            line_number=vuln_data.get("line_number"),
                            description=vuln_data.get("description", "N/A"),
                            recommendation=vuln_data.get("recommendation", "N/A")
                        )
                        vulnerabilities.append(vuln)
                    except ValueError as ve:
                        print(f"Skipping vulnerability due to invalid type: {vuln_data.get('type')}. Error: {ve}")
                        continue  # Skip this vulnerability if type is invalid
                    except Exception as e:
                        print(f"Error processing vulnerability data: {vuln_data}. Error: {e}")
                        continue

            gas_function_analysis_list = []
            if analysis_data.get("gas_analysis_per_function"):
                for gas_data in analysis_data.get("gas_analysis_per_function", []):
                    gas_item = GasFunctionAnalysis(
                        function_name=gas_data.get("function_name", "unknown_function"),
                        original_gas=gas_data.get("original_gas")
                        # optimized_gas, savings_absolute, savings_percentage might be filled by Gemini or calculated later
                    )
                    gas_function_analysis_list.append(gas_item)

            # Estimate deployment gas using Web3 for the original contract
            # This might be part of a more comprehensive gas analysis by Gemini too
            compilation_success_original, estimated_deployment_gas_original = await self.web3_service.compile_and_estimate_gas(contract_input.source_code, contract_input.compiler_version)

            analysis_report = AnalysisReport(
                vulnerabilities=vulnerabilities,
                gas_analysis_per_function=gas_function_analysis_list,
                overall_code_quality_score=analysis_data.get("overall_code_quality_score"),
                overall_security_score=analysis_data.get("overall_security_score"),
                general_suggestions=analysis_data.get("general_suggestions", []),
                estimated_total_gas_original=estimated_deployment_gas_original
            )

            processing_time_seconds = time.time() - start_time

            return ContractOutput(
                request_id=request_id,
                original_code=contract_input.source_code,
                analysis_report=analysis_report,
                compilation_success_original=compilation_success_original,
                confidence_score=analysis_data.get("confidence_score", 0.85),  # Gemini might provide this
                processing_time_seconds=processing_time_seconds,
                message="Contract analysis completed successfully."
            )

        except Exception as e:
            processing_time_seconds = time.time() - start_time
            error_analysis_report = AnalysisReport(
                general_suggestions=[f"Analysis failed: {str(e)}"]
            )
            return ContractOutput(
                request_id=request_id,
                original_code=contract_input.source_code,
                analysis_report=error_analysis_report,
                compilation_success_original=False,
                confidence_score=0.0,
                processing_time_seconds=processing_time_seconds,
                message=f"Analysis failed: {str(e)}"
            )

    async def process_contract_optimization(self, optimization_request: OptimizationRequest) -> ContractOutput:
        """Rewrite and optimize a smart contract using Gemini AI and Web3"""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Get rewritten contract and initial analysis from Gemini
            rewrite_data = await self.gemini_service.rewrite_contract(
                optimization_request.source_code,
                optimization_request.contract_name,
                [goal.value for goal in optimization_request.optimization_goals]
            )

            rewritten_code = rewrite_data.get("rewritten_code", optimization_request.source_code)

            # Compile and estimate gas for both versions
            compilation_success_original, gas_original = await self.web3_service.compile_and_estimate_gas(optimization_request.source_code, optimization_request.compiler_version)
            compilation_success_rewritten, gas_rewritten = await self.web3_service.compile_and_estimate_gas(rewritten_code, optimization_request.compiler_version)  # Assuming same compiler version

            # --- Populate AnalysisReport (can be from Gemini or re-calculated) ---
            # This part might be largely based on what Gemini's rewrite_contract returns for analysis
            vulnerabilities_in_rewritten = []  # Ideally, Gemini confirms fixes or new analysis
            if rewrite_data.get("analysis_of_rewritten_code", {}).get("vulnerabilities"):
                for vuln_data in rewrite_data.get("analysis_of_rewritten_code", {}).get("vulnerabilities", []):
                    try:
                        vuln_type_str = vuln_data.get("type")
                        vuln_type = VulnerabilityType(vuln_type_str) if vuln_type_str in VulnerabilityType.__members__ else VulnerabilityType.LOGIC_ERRORS
                        vuln = VulnerabilityInfo(
                            type=vuln_type,
                            severity=vuln_data.get("severity", "Medium"),
                            line_number=vuln_data.get("line_number"),
                            description=vuln_data.get("description", "N/A"),
                            recommendation=vuln_data.get("recommendation", "N/A")
                        )
                        vulnerabilities_in_rewritten.append(vuln)
                    except: continue

            gas_analysis_list_for_report = []
            # Example: if Gemini provides per-function gas for rewritten code
            if rewrite_data.get("analysis_of_rewritten_code", {}).get("gas_analysis_per_function"):
                for gas_data in rewrite_data.get("analysis_of_rewritten_code", {}).get("gas_analysis_per_function", []):
                     gas_analysis_list_for_report.append(GasFunctionAnalysis(**gas_data))
            # Or, at least, the deployment gas comparison
            else:
                gas_analysis_list_for_report.append(GasFunctionAnalysis(
                    function_name="contract_deployment",
                    original_gas=gas_original,
                    optimized_gas=gas_rewritten,
                    savings_absolute=(gas_original - gas_rewritten) if gas_original and gas_rewritten else None,
                    savings_percentage=(((gas_original - gas_rewritten) / gas_original) * 100) if gas_original and gas_rewritten and gas_original > 0 else None
                ))

            analysis_report_for_output = AnalysisReport(
                vulnerabilities=vulnerabilities_in_rewritten,  # Vulnerabilities in the *rewritten* code
                gas_analysis_per_function=gas_analysis_list_for_report,
                overall_code_quality_score=rewrite_data.get("analysis_of_rewritten_code", {}).get("overall_code_quality_score"),
                overall_security_score=rewrite_data.get("analysis_of_rewritten_code", {}).get("overall_security_score"),
                general_suggestions=rewrite_data.get("analysis_of_rewritten_code", {}).get("general_suggestions", []),
                estimated_total_gas_original=gas_original,
                estimated_total_gas_optimized=gas_rewritten,
                total_gas_savings_absolute=(gas_original - gas_rewritten) if gas_original and gas_rewritten else None,
                total_gas_savings_percentage=(((gas_original - gas_rewritten) / gas_original) * 100) if gas_original and gas_rewritten and gas_original > 0 else None
            )

            # --- Populate RewriteReport ---
            rewrite_report_for_output = RewriteReport(
                changes_summary=rewrite_data.get("changes_summary", []),
                security_enhancements_made=rewrite_data.get("security_enhancements_made", []),
                readability_notes=rewrite_data.get("readability_notes")
            )

            processing_time_seconds = time.time() - start_time

            return ContractOutput(
                request_id=request_id,
                original_code=optimization_request.source_code,
                rewritten_code=rewritten_code,
                analysis_report=analysis_report_for_output,
                rewrite_report=rewrite_report_for_output,
                compilation_success_original=compilation_success_original,
                compilation_success_rewritten=compilation_success_rewritten,
                diff_summary=rewrite_data.get("diff_summary"),  # Gemini might provide a textual diff
                confidence_score=rewrite_data.get("confidence_score", 0.8),
                processing_time_seconds=processing_time_seconds,
                message="Contract optimization completed successfully."
            )

        except Exception as e:
            processing_time_seconds = time.time() - start_time
            # Populate with minimal error info
            error_analysis_report = AnalysisReport(general_suggestions=[f"Optimization failed: {str(e)}"])
            return ContractOutput(
                request_id=request_id,
                original_code=optimization_request.source_code,
                analysis_report=error_analysis_report,
                compilation_success_original=None,  # Unknown at this point
                compilation_success_rewritten=False,
                confidence_score=0.0,
                processing_time_seconds=processing_time_seconds,
                message=f"Optimization failed: {str(e)}"
            )

    # _generate_diff_summary might be replaced by Gemini's diff or a proper library
    # def _generate_diff_summary(self, changes_made: list) -> str:
    #     ...

# Service instances
contract_service = ContractProcessingService()
