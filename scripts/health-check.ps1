# Smart Contract Rewriter - Health Check & Debug Script

param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000",
    [switch]$Detailed,
    [switch]$Fix
)

Write-Host "🏥 Smart Contract Rewriter - Health Check & Debug" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

function Test-ServiceHealth {
    param([string]$Url, [string]$ServiceName)
    
    Write-Host "🔍 Testing $ServiceName ($Url)..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "$Url/health" -Method GET -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $ServiceName is healthy!" -ForegroundColor Green
            if ($Detailed) {
                Write-Host "   Response: $($response.Content)" -ForegroundColor Gray
            }
            return $true
        }
    } catch {
        Write-Host "❌ $ServiceName health check failed!" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($_.Exception -like "*connection*") {
            Write-Host "   💡 Service might not be running" -ForegroundColor Yellow
        } elseif ($_.Exception -like "*timeout*") {
            Write-Host "   💡 Service is slow to respond" -ForegroundColor Yellow
        }
        return $false
    }
}

function Test-DatabaseConnection {
    Write-Host "🗄️  Testing database connection..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "$BackendUrl/health" -Method GET
        $healthData = $response.Content | ConvertFrom-Json
        
        if ($healthData.database_status -eq "healthy") {
            Write-Host "✅ Database connection is healthy!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Database connection failed!" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Cannot check database status!" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-ApiEndpoints {
    Write-Host "🌐 Testing API endpoints..." -ForegroundColor Yellow
    
    $endpoints = @(
        @{Path="/health"; Method="GET"; Description="Health Check"},
        @{Path="/api/v1/contracts/analyze"; Method="POST"; Description="Contract Analysis"},
        @{Path="/api/v1/contracts/rewrite"; Method="POST"; Description="Contract Rewrite"},
        @{Path="/api/v1/contracts/history"; Method="GET"; Description="Contract History"}
    )
    
    $successCount = 0
    
    foreach ($endpoint in $endpoints) {
        try {
            if ($endpoint.Method -eq "GET") {
                $response = Invoke-WebRequest -Uri "$BackendUrl$($endpoint.Path)" -Method $endpoint.Method -TimeoutSec 5
            } else {
                # For POST endpoints, just check if they're reachable (they might return 422 for missing data)
                $response = Invoke-WebRequest -Uri "$BackendUrl$($endpoint.Path)" -Method $endpoint.Method -TimeoutSec 5 -ErrorAction SilentlyContinue
            }
            
            if ($response.StatusCode -in @(200, 422)) {  # 422 is expected for POST without data
                Write-Host "   ✅ $($endpoint.Description)" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "   ❌ $($endpoint.Description) - Status: $($response.StatusCode)" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ❌ $($endpoint.Description) - Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "📊 API Endpoints: $successCount/$($endpoints.Count) working" -ForegroundColor Cyan
    return $successCount -eq $endpoints.Count
}

function Check-Dependencies {
    Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
    
    # Check if Docker is running
    try {
        docker version | Out-Null
        Write-Host "   ✅ Docker is running" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Docker is not running" -ForegroundColor Red
    }
    
    # Check if PostgreSQL is accessible
    try {
        docker ps --filter "name=postgres" --format "table {{.Names}}\t{{.Status}}" | Out-Host
        Write-Host "   ✅ PostgreSQL container found" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ PostgreSQL container not found" -ForegroundColor Red
    }
    
    # Check Python environment
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "   ✅ Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Python not found" -ForegroundColor Red
    }
    
    # Check Node.js environment
    try {
        $nodeVersion = node --version 2>&1
        Write-Host "   ✅ Node.js: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Node.js not found" -ForegroundColor Red
    }
}

function Show-TroubleshootingTips {
    Write-Host ""
    Write-Host "🛠️  Troubleshooting Tips:" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "❌ If Backend is not responding:" -ForegroundColor Yellow
    Write-Host "   • Check if backend is running: uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "   • Verify database is running: docker-compose up -d db" -ForegroundColor White
    Write-Host "   • Check backend logs for errors" -ForegroundColor White
    Write-Host "   • Ensure .env file has correct DATABASE_URL" -ForegroundColor White
    Write-Host ""
    Write-Host "❌ If Frontend is not responding:" -ForegroundColor Yellow
    Write-Host "   • Check if frontend is running: npm run dev" -ForegroundColor White
    Write-Host "   • Verify VITE_API_BASE_URL in .env" -ForegroundColor White
    Write-Host "   • Check browser console for errors" -ForegroundColor White
    Write-Host ""
    Write-Host "❌ If Database connection fails:" -ForegroundColor Yellow
    Write-Host "   • Ensure PostgreSQL is running: docker-compose up -d db" -ForegroundColor White
    Write-Host "   • Check DATABASE_URL format in .env" -ForegroundColor White
    Write-Host "   • Run database migrations: alembic upgrade head" -ForegroundColor White
    Write-Host ""
    Write-Host "❌ If API endpoints return errors:" -ForegroundColor Yellow
    Write-Host "   • Check for missing GEMINI_API_KEY" -ForegroundColor White
    Write-Host "   • Verify CORS settings in backend" -ForegroundColor White
    Write-Host "   • Check request format and headers" -ForegroundColor White
}

function Auto-Fix-Issues {
    Write-Host "🔧 Attempting to auto-fix common issues..." -ForegroundColor Yellow
    
    # Start database if not running
    Write-Host "   🗄️  Starting database..." -ForegroundColor Gray
    docker-compose up -d db
    Start-Sleep -Seconds 5
    
    # Install/update dependencies
    Write-Host "   📦 Checking backend dependencies..." -ForegroundColor Gray
    Push-Location "backend"
    try {
        pip install -r requirements.txt
        Write-Host "   ✅ Backend dependencies updated" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Failed to install backend dependencies" -ForegroundColor Red
    }
    Pop-Location
    
    Write-Host "   📦 Checking frontend dependencies..." -ForegroundColor Gray
    Push-Location "frontend"
    try {
        npm install
        Write-Host "   ✅ Frontend dependencies updated" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Failed to install frontend dependencies" -ForegroundColor Red
    }
    Pop-Location
    
    # Run database migrations
    Write-Host "   🔄 Running database migrations..." -ForegroundColor Gray
    Push-Location "backend"
    try {
        alembic upgrade head
        Write-Host "   ✅ Database migrations completed" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Database migration failed" -ForegroundColor Red
    }
    Pop-Location
    
    Write-Host "   🔧 Auto-fix completed!" -ForegroundColor Green
}

# Main execution
Write-Host "Starting comprehensive health check..." -ForegroundColor Cyan
Write-Host ""

$backendHealthy = Test-ServiceHealth -Url $BackendUrl -ServiceName "Backend"
$frontendHealthy = Test-ServiceHealth -Url $FrontendUrl -ServiceName "Frontend"

if ($backendHealthy) {
    $dbHealthy = Test-DatabaseConnection
    $apiHealthy = Test-ApiEndpoints
} else {
    $dbHealthy = $false
    $apiHealthy = $false
}

Check-Dependencies

Write-Host ""
Write-Host "📊 Overall Health Summary:" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host "Backend:    $(if($backendHealthy){'✅ Healthy'}else{'❌ Unhealthy'})" -ForegroundColor $(if($backendHealthy){'Green'}else{'Red'})
Write-Host "Frontend:   $(if($frontendHealthy){'✅ Healthy'}else{'❌ Unhealthy'})" -ForegroundColor $(if($frontendHealthy){'Green'}else{'Red'})
Write-Host "Database:   $(if($dbHealthy){'✅ Healthy'}else{'❌ Unhealthy'})" -ForegroundColor $(if($dbHealthy){'Green'}else{'Red'})
Write-Host "API:        $(if($apiHealthy){'✅ Healthy'}else{'❌ Unhealthy'})" -ForegroundColor $(if($apiHealthy){'Green'}else{'Red'})

if ($Fix -and (!$backendHealthy -or !$frontendHealthy -or !$dbHealthy)) {
    Write-Host ""
    Auto-Fix-Issues
    
    # Re-run health checks
    Write-Host ""
    Write-Host "🔄 Re-running health checks after auto-fix..." -ForegroundColor Yellow
    $backendHealthy = Test-ServiceHealth -Url $BackendUrl -ServiceName "Backend"
    if ($backendHealthy) {
        $dbHealthy = Test-DatabaseConnection
    }
}

if (!$backendHealthy -or !$frontendHealthy -or !$dbHealthy -or !$apiHealthy) {
    Show-TroubleshootingTips
}
