# Smart Contract Rewriter - Performance Testing Script
# This script performs load testing and performance analysis

param(
    [string]$BaseUrl = "http://localhost:8000",
    [int]$ConcurrentUsers = 10,
    [int]$Duration = 60,
    [string]$TestType = "load",  # load, stress, spike, volume
    [switch]$GenerateReport
)

# Global variables
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$LogFile = Join-Path $ProjectRoot "logs/performance-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$ReportPath = Join-Path $ProjectRoot "reports/performance"

# Ensure directories exist
New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "logs") | Out-Null
New-Item -ItemType Directory -Force -Path $ReportPath | Out-Null

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Check if service is available
function Test-ServiceAvailability {
    Write-Log "Checking service availability at $BaseUrl"
    
    try {
        $Response = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -TimeoutSec 10
        if ($Response.status -eq "healthy") {
            Write-Log "Service is healthy and ready for testing"
            return $true
        }
    }
    catch {
        Write-Log "Service is not available: $_" "ERROR"
        return $false
    }
}

# Create test contract for load testing
function Get-TestContract {
    return @"
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 private value;
    
    function setValue(uint256 _value) public {
        value = _value;
    }
    
    function getValue() public view returns (uint256) {
        return value;
    }
}
"@
}

# Performance test scenarios
function Start-LoadTest {
    Write-Log "Starting load test with $ConcurrentUsers concurrent users for $Duration seconds"
    
    $TestContract = Get-TestContract
    $Results = @()
    $Jobs = @()
    
    # Create test jobs
    for ($i = 1; $i -le $ConcurrentUsers; $i++) {
        $Job = Start-Job -ScriptBlock {
            param($BaseUrl, $Duration, $UserIndex, $TestContract)
            
            $Results = @()
            $EndTime = (Get-Date).AddSeconds($Duration)
            $RequestCount = 0
            
            while ((Get-Date) -lt $EndTime) {
                $StartTime = Get-Date
                
                try {
                    # Test contract rewriting API
                    $Body = @{
                        contract_code = $TestContract
                        improvement_type = "gas_optimization"
                        description = "Load test request from user $UserIndex"
                    } | ConvertTo-Json
                    
                    $Response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/contracts/rewrite" -Method POST -Body $Body -ContentType "application/json" -TimeoutSec 30
                    
                    $ResponseTime = (Get-Date) - $StartTime
                    $RequestCount++
                    
                    $Results += @{
                        User = $UserIndex
                        RequestNumber = $RequestCount
                        ResponseTime = $ResponseTime.TotalMilliseconds
                        Success = $true
                        Timestamp = Get-Date
                    }
                }
                catch {
                    $ResponseTime = (Get-Date) - $StartTime
                    $RequestCount++
                    
                    $Results += @{
                        User = $UserIndex
                        RequestNumber = $RequestCount
                        ResponseTime = $ResponseTime.TotalMilliseconds
                        Success = $false
                        Error = $_.Exception.Message
                        Timestamp = Get-Date
                    }
                }
                
                # Small delay to prevent overwhelming
                Start-Sleep -Milliseconds 100
            }
            
            return $Results
        } -ArgumentList $BaseUrl, $Duration, $i, $TestContract
        
        $Jobs += $Job
    }
    
    # Wait for all jobs to complete
    Write-Log "Waiting for load test to complete..."
    $Jobs | Wait-Job | Out-Null
    
    # Collect results
    foreach ($Job in $Jobs) {
        $JobResults = Receive-Job -Job $Job
        $Results += $JobResults
        Remove-Job -Job $Job
    }
    
    return $Results
}

# Stress test - gradually increase load
function Start-StressTest {
    Write-Log "Starting stress test - gradually increasing load"
    
    $AllResults = @()
    $MaxUsers = $ConcurrentUsers
    
    for ($Users = 1; $Users -le $MaxUsers; $Users += 2) {
        Write-Log "Testing with $Users concurrent users"
        
        # Run shorter duration tests with increasing load
        $StressResults = Start-LoadTest -ConcurrentUsers $Users -Duration 30
        $AllResults += $StressResults
        
        # Brief pause between test phases
        Start-Sleep 5
    }
    
    return $AllResults
}

# Spike test - sudden load increase
function Start-SpikeTest {
    Write-Log "Starting spike test"
    
    $AllResults = @()
    
    # Normal load
    Write-Log "Phase 1: Normal load (2 users)"
    $Phase1 = Start-LoadTest -ConcurrentUsers 2 -Duration 30
    $AllResults += $Phase1
    
    # Spike
    Write-Log "Phase 2: Spike load ($ConcurrentUsers users)"
    $Phase2 = Start-LoadTest -ConcurrentUsers $ConcurrentUsers -Duration 60
    $AllResults += $Phase2
    
    # Return to normal
    Write-Log "Phase 3: Return to normal (2 users)"
    $Phase3 = Start-LoadTest -ConcurrentUsers 2 -Duration 30
    $AllResults += $Phase3
    
    return $AllResults
}

# Analyze results
function Analyze-Results {
    param([array]$Results)
    
    Write-Log "Analyzing performance test results..."
    
    $SuccessfulRequests = $Results | Where-Object { $_.Success -eq $true }
    $FailedRequests = $Results | Where-Object { $_.Success -eq $false }
    
    $TotalRequests = $Results.Count
    $SuccessRate = ($SuccessfulRequests.Count / $TotalRequests) * 100
    $FailureRate = ($FailedRequests.Count / $TotalRequests) * 100
    
    $ResponseTimes = $SuccessfulRequests | ForEach-Object { $_.ResponseTime }
    
    $Analysis = @{
        TotalRequests = $TotalRequests
        SuccessfulRequests = $SuccessfulRequests.Count
        FailedRequests = $FailedRequests.Count
        SuccessRate = [math]::Round($SuccessRate, 2)
        FailureRate = [math]::Round($FailureRate, 2)
        AverageResponseTime = if ($ResponseTimes) { [math]::Round(($ResponseTimes | Measure-Object -Average).Average, 2) } else { 0 }
        MinResponseTime = if ($ResponseTimes) { [math]::Round(($ResponseTimes | Measure-Object -Minimum).Minimum, 2) } else { 0 }
        MaxResponseTime = if ($ResponseTimes) { [math]::Round(($ResponseTimes | Measure-Object -Maximum).Maximum, 2) } else { 0 }
        MedianResponseTime = if ($ResponseTimes) { [math]::Round((($ResponseTimes | Sort-Object)[[math]::Floor($ResponseTimes.Length / 2)]), 2) } else { 0 }
        Percentile95 = if ($ResponseTimes) { [math]::Round((($ResponseTimes | Sort-Object)[[math]::Floor($ResponseTimes.Length * 0.95)]), 2) } else { 0 }
        Percentile99 = if ($ResponseTimes) { [math]::Round((($ResponseTimes | Sort-Object)[[math]::Floor($ResponseTimes.Length * 0.99)]), 2) } else { 0 }
        RequestsPerSecond = [math]::Round($TotalRequests / $Duration, 2)
    }
    
    return $Analysis
}

# Generate HTML report
function Generate-HtmlReport {
    param([array]$Results, [hashtable]$Analysis)
    
    Write-Log "Generating HTML performance report..."
    
    $ReportFile = Join-Path $ReportPath "performance-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').html"
    
    $HtmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <title>Smart Contract Rewriter - Performance Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric-card { background-color: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007acc; }
        .metric-label { font-size: 14px; color: #666; margin-top: 5px; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f4f4f4; }
        .chart-container { margin: 20px 0; height: 400px; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="header">
        <h1>Performance Test Report</h1>
        <p><strong>Test Type:</strong> $TestType</p>
        <p><strong>Base URL:</strong> $BaseUrl</p>
        <p><strong>Concurrent Users:</strong> $ConcurrentUsers</p>
        <p><strong>Duration:</strong> $Duration seconds</p>
        <p><strong>Generated:</strong> $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>
    </div>

    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value">$($Analysis.TotalRequests)</div>
            <div class="metric-label">Total Requests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value success">$($Analysis.SuccessRate)%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">$($Analysis.AverageResponseTime) ms</div>
            <div class="metric-label">Avg Response Time</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">$($Analysis.RequestsPerSecond)</div>
            <div class="metric-label">Requests/Second</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">$($Analysis.MedianResponseTime) ms</div>
            <div class="metric-label">Median Response Time</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">$($Analysis.Percentile95) ms</div>
            <div class="metric-label">95th Percentile</div>
        </div>
    </div>

    <h2>Response Time Distribution</h2>
    <div class="chart-container">
        <canvas id="responseTimeChart"></canvas>
    </div>

    <h2>Summary Statistics</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total Requests</td><td>$($Analysis.TotalRequests)</td></tr>
        <tr><td>Successful Requests</td><td class="success">$($Analysis.SuccessfulRequests)</td></tr>
        <tr><td>Failed Requests</td><td class="error">$($Analysis.FailedRequests)</td></tr>
        <tr><td>Success Rate</td><td>$($Analysis.SuccessRate)%</td></tr>
        <tr><td>Average Response Time</td><td>$($Analysis.AverageResponseTime) ms</td></tr>
        <tr><td>Minimum Response Time</td><td>$($Analysis.MinResponseTime) ms</td></tr>
        <tr><td>Maximum Response Time</td><td>$($Analysis.MaxResponseTime) ms</td></tr>
        <tr><td>Median Response Time</td><td>$($Analysis.MedianResponseTime) ms</td></tr>
        <tr><td>95th Percentile</td><td>$($Analysis.Percentile95) ms</td></tr>
        <tr><td>99th Percentile</td><td>$($Analysis.Percentile99) ms</td></tr>
        <tr><td>Requests per Second</td><td>$($Analysis.RequestsPerSecond)</td></tr>
    </table>

    <script>
        // Response time chart
        const ctx = document.getElementById('responseTimeChart').getContext('2d');
        const responseTimeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [$(($Results | ForEach-Object { "'$($_.Timestamp.ToString('HH:mm:ss'))'" }) -join ',')],
                datasets: [{
                    label: 'Response Time (ms)',
                    data: [$(($Results | ForEach-Object { $_.ResponseTime }) -join ',')],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Response Time (ms)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"@

    Set-Content -Path $ReportFile -Value $HtmlContent
    Write-Log "HTML report generated: $ReportFile"
    
    return $ReportFile
}

# Main execution
try {
    Write-Log "Starting performance testing for Smart Contract Rewriter"
    Write-Log "Test Type: $TestType, Base URL: $BaseUrl, Users: $ConcurrentUsers, Duration: $Duration seconds"
    
    # Check service availability
    if (-not (Test-ServiceAvailability)) {
        throw "Service is not available for testing"
    }
    
    # Run appropriate test type
    $Results = switch ($TestType.ToLower()) {
        "load" { Start-LoadTest }
        "stress" { Start-StressTest }
        "spike" { Start-SpikeTest }
        default { Start-LoadTest }
    }
    
    # Analyze results
    $Analysis = Analyze-Results -Results $Results
    
    # Display results
    Write-Log ""
    Write-Log "=== PERFORMANCE TEST RESULTS ==="
    Write-Log "Total Requests: $($Analysis.TotalRequests)"
    Write-Log "Success Rate: $($Analysis.SuccessRate)%"
    Write-Log "Average Response Time: $($Analysis.AverageResponseTime) ms"
    Write-Log "Requests per Second: $($Analysis.RequestsPerSecond)"
    Write-Log "95th Percentile: $($Analysis.Percentile95) ms"
    
    # Generate report if requested
    if ($GenerateReport) {
        $ReportFile = Generate-HtmlReport -Results $Results -Analysis $Analysis
        Write-Log "Performance report available at: $ReportFile"
        
        # Open report in browser
        if (Test-Path $ReportFile) {
            Start-Process $ReportFile
        }
    }
    
    # Export results to CSV
    $CsvFile = Join-Path $ReportPath "performance-results-$(Get-Date -Format 'yyyyMMdd-HHmmss').csv"
    $Results | Export-Csv -Path $CsvFile -NoTypeInformation
    Write-Log "Raw results exported to: $CsvFile"
    
    Write-Log "Performance testing completed successfully!"
    
} catch {
    Write-Log "Performance testing failed: $_" "ERROR"
    exit 1
}
