#!/usr/bin/env pwsh
# Smart Contract Rewriter - Test Backend Fixes Script

Write-Host "🧪 Testing Smart Contract Rewriter Backend Fixes" -ForegroundColor Cyan
Write-Host "=" * 50

# Configuration
$BASE_URL = "http://localhost:8000"
$API_URL = "$BASE_URL/api/v1"

function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [string]$Description,
        [hashtable]$Body = $null
    )
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "✓ $Description - Status: Success" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "✗ $Description - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Test 1: Health Check
Write-Host "`n1. Testing Health Check..." -ForegroundColor Yellow
$health = Test-Endpoint -Url "$BASE_URL/health" -Description "Backend Health Check"

if (-not $health) {
    Write-Host "❌ Backend is not running. Please start with:" -ForegroundColor Red
    Write-Host "   docker-compose up -d" -ForegroundColor White
    Write-Host "   cd backend && uvicorn app.main:app --reload" -ForegroundColor White
    exit 1
}

# Test 2: Contract History Endpoint
Write-Host "`n2. Testing Contract History Endpoint..." -ForegroundColor Yellow
$history = Test-Endpoint -Url "$API_URL/contracts/history" -Description "Contract History"

if ($history) {
    Write-Host "✓ Found $($history.Count) contracts in history" -ForegroundColor Green
    
    if ($history.Count -gt 0) {
        $firstContract = $history[0]
        Write-Host "✓ First contract structure:" -ForegroundColor Green
        Write-Host "  - ID: $($firstContract.id)" -ForegroundColor White
        Write-Host "  - Type: $($firstContract.type)" -ForegroundColor White
        Write-Host "  - Name: $($firstContract.contract_name)" -ForegroundColor White
        Write-Host "  - Success: $($firstContract.success)" -ForegroundColor White
        
        $details = $firstContract.details
        if ($details) {
            Write-Host "  - Details keys: $($details.PSObject.Properties.Name -join ', ')" -ForegroundColor White
            
            if ($firstContract.type -eq "analysis") {
                $vulnCount = $details.vulnerabilities_count
                Write-Host "  - Vulnerabilities: $vulnCount" -ForegroundColor White
            }
            elseif ($firstContract.type -eq "rewrite") {
                $gasSavings = $details.gas_savings_percentage
                $changes = $details.changes_count
                Write-Host "  - Gas Savings: $gasSavings%" -ForegroundColor White
                Write-Host "  - Changes: $changes" -ForegroundColor White
            }
        }
    }
}

# Test 3: Delete Endpoint (with non-existent ID)
Write-Host "`n3. Testing Delete Endpoint..." -ForegroundColor Yellow
$deleteResult = Test-Endpoint -Url "$API_URL/contracts/history/999999" -Method "DELETE" -Description "Delete Non-existent Contract"

# Test 4: Sample Contract Analysis (if Gemini API key is available)
Write-Host "`n4. Testing Sample Analysis..." -ForegroundColor Yellow
$sampleContract = @{
    source_code = @"
pragma solidity ^0.8.0;
contract SimpleStorage {
    uint256 private storedData;
    function set(uint256 x) public { storedData = x; }
    function get() public view returns (uint256) { return storedData; }
}
"@
    contract_name = "TestContract"
    compiler_version = "0.8.19"
}

$analysisResult = Test-Endpoint -Url "$API_URL/contracts/analyze" -Method "POST" -Body $sampleContract -Description "Sample Contract Analysis"

if ($analysisResult) {
    Write-Host "✓ Analysis completed successfully!" -ForegroundColor Green
    Write-Host "  - Request ID: $($analysisResult.request_id)" -ForegroundColor White
    Write-Host "  - Processing Time: $($analysisResult.processing_time_seconds)s" -ForegroundColor White
    Write-Host "  - Message: $($analysisResult.message)" -ForegroundColor White
    
    if ($analysisResult.analysis_report) {
        $report = $analysisResult.analysis_report
        Write-Host "  - Vulnerabilities: $($report.vulnerabilities.Count)" -ForegroundColor White
        Write-Host "  - Quality Score: $($report.overall_code_quality_score)" -ForegroundColor White
        Write-Host "  - Security Score: $($report.overall_security_score)" -ForegroundColor White
    }
}

# Test 5: Re-check History for New Data
Write-Host "`n5. Re-checking History for New Data..." -ForegroundColor Yellow
$newHistory = Test-Endpoint -Url "$API_URL/contracts/history" -Description "Updated Contract History"

if ($newHistory -and $newHistory.Count -gt ($history.Count)) {
    Write-Host "✓ New contract added to history!" -ForegroundColor Green
    Write-Host "✓ History now contains $($newHistory.Count) contracts" -ForegroundColor Green
}

Write-Host "`n✅ Backend Testing Completed!" -ForegroundColor Green
Write-Host "`n📋 Summary:" -ForegroundColor Cyan
Write-Host "- Health Check: $(if($health) {'✓ Passed'} else {'✗ Failed'})" 
Write-Host "- History Endpoint: $(if($history) {'✓ Passed'} else {'✗ Failed'})"
Write-Host "- Delete Endpoint: $(if($deleteResult -ne $null) {'✓ Passed'} else {'✗ Failed'})"
Write-Host "- Sample Analysis: $(if($analysisResult) {'✓ Passed'} else {'✗ Failed (check Gemini API key)'})"

Write-Host "`n🌐 Frontend Testing:" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Go to Contract History page" -ForegroundColor White
Write-Host "3. Verify that numbers show real values (not zeros)" -ForegroundColor White
Write-Host "4. Test delete functionality with trash icon" -ForegroundColor White
Write-Host "5. Test download functionality for contract files" -ForegroundColor White
