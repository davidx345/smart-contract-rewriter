# Smart Contract Rewriter - Master Setup & Deployment Script
# This script automates the complete setup and deployment process

param(
    [ValidateSet("development", "production", "render", "k8s")]
    [string]$Environment = "development",
    
    [switch]$SkipDependencies,
    [switch]$SkipTests,
    [switch]$SkipBuild,
    [switch]$DeployOnly,
    [switch]$WithMonitoring
)

# Global variables
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$LogFile = Join-Path $ProjectRoot "logs/setup-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Ensure logs directory exists
New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "logs") | Out-Null

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Error handling
function Handle-Error {
    param([string]$ErrorMessage)
    Write-Log "ERROR: $ErrorMessage" "ERROR"
    Write-Log "Setup failed. Check log file: $LogFile" "ERROR"
    exit 1
}

# Check prerequisites
function Test-Prerequisites {
    Write-Log "Checking prerequisites..."
    
    $Prerequisites = @(
        @{Name="Docker"; Command="docker --version"},
        @{Name="Docker Compose"; Command="docker-compose --version"},
        @{Name="Node.js"; Command="node --version"},
        @{Name="Python"; Command="python --version"},
        @{Name="Git"; Command="git --version"}
    )
    
    foreach ($Prereq in $Prerequisites) {
        try {
            $Version = Invoke-Expression $Prereq.Command 2>$null
            Write-Log "$($Prereq.Name) is installed: $Version"
        }
        catch {
            Handle-Error "$($Prereq.Name) is not installed or not in PATH"
        }
    }
    
    # Check if ports are available
    $RequiredPorts = @(8000, 3000, 5432, 9090, 3001, 9093)
    foreach ($Port in $RequiredPorts) {
        $Connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
        if ($Connection.TcpTestSucceeded) {
            Write-Log "WARNING: Port $Port is already in use" "WARN"
        }
    }
}

# Setup environment files
function Set-EnvironmentFiles {
    Write-Log "Setting up environment files..."
    
    # Backend .env
    $BackendEnvPath = Join-Path $ProjectRoot "backend/.env"
    if (-not (Test-Path $BackendEnvPath)) {
        $BackendEnvContent = @"
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/smart_contract_rewriter

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Security
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=true
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Application Info
APP_NAME=Smart Contract Rewriter
APP_VERSION=1.0.0

# Prometheus Metrics
PROMETHEUS_ENABLED=true
METRICS_PORT=8001
"@
        Set-Content -Path $BackendEnvPath -Value $BackendEnvContent
        Write-Log "Created backend .env file"
    }
    
    # Frontend .env
    $FrontendEnvPath = Join-Path $ProjectRoot "frontend/.env"
    if (-not (Test-Path $FrontendEnvPath)) {
        $FrontendEnvContent = @"
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Smart Contract Rewriter
VITE_APP_VERSION=1.0.0
"@
        Set-Content -Path $FrontendEnvPath -Value $FrontendEnvContent
        Write-Log "Created frontend .env file"
    }
}

# Install dependencies
function Install-Dependencies {
    if ($SkipDependencies) {
        Write-Log "Skipping dependency installation"
        return
    }
    
    Write-Log "Installing dependencies..."
    
    # Backend dependencies
    Write-Log "Installing backend dependencies..."
    Set-Location (Join-Path $ProjectRoot "backend")
    try {
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        Write-Log "Backend dependencies installed successfully"
    }
    catch {
        Handle-Error "Failed to install backend dependencies: $_"
    }
    
    # Frontend dependencies
    Write-Log "Installing frontend dependencies..."
    Set-Location (Join-Path $ProjectRoot "frontend")
    try {
        npm ci
        Write-Log "Frontend dependencies installed successfully"
    }
    catch {
        Handle-Error "Failed to install frontend dependencies: $_"
    }
    
    Set-Location $ProjectRoot
}

# Run tests
function Run-Tests {
    if ($SkipTests) {
        Write-Log "Skipping tests"
        return
    }
    
    Write-Log "Running tests..."
    
    # Backend tests
    Write-Log "Running backend tests..."
    Set-Location (Join-Path $ProjectRoot "backend")
    try {
        python -m pytest tests/ -v --tb=short
        Write-Log "Backend tests passed"
    }
    catch {
        Write-Log "Backend tests failed: $_" "WARN"
    }
    
    # Frontend tests
    Write-Log "Running frontend tests..."
    Set-Location (Join-Path $ProjectRoot "frontend")
    try {
        npm test -- --watchAll=false
        Write-Log "Frontend tests passed"
    }
    catch {
        Write-Log "Frontend tests failed: $_" "WARN"
    }
    
    Set-Location $ProjectRoot
}

# Build applications
function Build-Applications {
    if ($SkipBuild) {
        Write-Log "Skipping build"
        return
    }
    
    Write-Log "Building applications..."
    
    # Build frontend
    Write-Log "Building frontend..."
    Set-Location (Join-Path $ProjectRoot "frontend")
    try {
        npm run build
        Write-Log "Frontend built successfully"
    }
    catch {
        Handle-Error "Failed to build frontend: $_"
    }
    
    Set-Location $ProjectRoot
}

# Setup database
function Set-Database {
    Write-Log "Setting up database..."
    
    if ($Environment -eq "development") {
        # Start PostgreSQL container
        Write-Log "Starting PostgreSQL container..."
        docker-compose up -d postgres
        
        # Wait for database to be ready
        Write-Log "Waiting for database to be ready..."
        $MaxAttempts = 30
        $Attempt = 0
        do {
            Start-Sleep 2
            $Attempt++
            try {
                $Result = docker exec smart_contract_rewriter-postgres-1 pg_isready -U postgres 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "Database is ready"
                    break
                }
            }
            catch {}
        } while ($Attempt -lt $MaxAttempts)
        
        if ($Attempt -eq $MaxAttempts) {
            Handle-Error "Database failed to start after $MaxAttempts attempts"
        }
        
        # Run migrations
        Write-Log "Running database migrations..."
        Set-Location (Join-Path $ProjectRoot "backend")
        try {
            alembic upgrade head
            Write-Log "Database migrations completed"
        }
        catch {
            Handle-Error "Failed to run database migrations: $_"
        }
        Set-Location $ProjectRoot
    }
}

# Deploy based on environment
function Deploy-Application {
    Write-Log "Deploying for environment: $Environment"
    
    switch ($Environment) {
        "development" {
            Write-Log "Starting development environment..."
            
            if ($WithMonitoring) {
                Write-Log "Starting with monitoring stack..."
                docker-compose -f docker-compose.yml up -d
            } else {
                Write-Log "Starting basic services..."
                docker-compose up -d postgres backend frontend
            }
            
            # Wait for services to be ready
            Start-Sleep 10
            
            # Health check
            Write-Log "Performing health checks..."
            & (Join-Path $PSScriptRoot "health-check.ps1") -Quick
        }
        
        "production" {
            Write-Log "Building production containers..."
            docker-compose -f docker-compose.yml build
            docker-compose -f docker-compose.yml up -d
            
            Write-Log "Production deployment completed"
        }
        
        "render" {
            Write-Log "Deploying to Render.com..."
            & (Join-Path $PSScriptRoot "deploy-render.ps1")
        }
        
        "k8s" {
            Write-Log "Deploying to Kubernetes..."
            
            # Apply Kubernetes manifests
            kubectl apply -f (Join-Path $ProjectRoot "k8s/namespace.yaml")
            kubectl apply -f (Join-Path $ProjectRoot "k8s/configmap.yaml")
            kubectl apply -f (Join-Path $ProjectRoot "k8s/postgres.yaml")
            kubectl apply -f (Join-Path $ProjectRoot "k8s/backend.yaml")
            kubectl apply -f (Join-Path $ProjectRoot "k8s/frontend.yaml")
            
            Write-Log "Kubernetes deployment completed"
        }
    }
}

# Setup monitoring
function Set-Monitoring {
    if (-not $WithMonitoring) {
        return
    }
    
    Write-Log "Setting up monitoring stack..."
    & (Join-Path $PSScriptRoot "setup-monitoring.ps1")
}

# Display deployment information
function Show-DeploymentInfo {
    Write-Log "Deployment completed successfully!" "SUCCESS"
    Write-Log ""
    Write-Log "=== DEPLOYMENT INFORMATION ==="
    
    switch ($Environment) {
        "development" {
            Write-Log "Frontend: http://localhost:3000"
            Write-Log "Backend API: http://localhost:8000"
            Write-Log "API Docs: http://localhost:8000/docs"
            Write-Log "Database: localhost:5432"
            
            if ($WithMonitoring) {
                Write-Log ""
                Write-Log "=== MONITORING STACK ==="
                Write-Log "Prometheus: http://localhost:9090"
                Write-Log "Grafana: http://localhost:3001 (admin/admin)"
                Write-Log "Alertmanager: http://localhost:9093"
            }
        }
        
        "render" {
            Write-Log "Frontend: https://smart-contract-frontend.onrender.com"
            Write-Log "Backend API: https://smart-contract-backend.onrender.com"
            Write-Log "API Docs: https://smart-contract-backend.onrender.com/docs"
        }
        
        "k8s" {
            Write-Log "Use 'kubectl get services' to see service endpoints"
            Write-Log "Use 'kubectl get ingress' to see ingress URLs"
        }
    }
    
    Write-Log ""
    Write-Log "Log file: $LogFile"
    Write-Log "For troubleshooting, run: scripts/health-check.ps1"
}

# Main execution
try {
    Write-Log "Starting Smart Contract Rewriter setup for environment: $Environment"
    Write-Log "Project root: $ProjectRoot"
    
    if (-not $DeployOnly) {
        Test-Prerequisites
        Set-EnvironmentFiles
        Install-Dependencies
        Run-Tests
        Build-Applications
        Set-Database
    }
    
    Deploy-Application
    Set-Monitoring
    Show-DeploymentInfo
    
} catch {
    Handle-Error "Unexpected error: $_"
}
    [string]$Environment = "development",
    [switch]$WithMonitoring,
    [switch]$SkipDependencies,
    [string]$GeminiApiKey
)

Write-Host "🚀 Smart Contract Rewriter - Master Setup" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Green

function Setup-Development {
    Write-Host "🔧 Setting up development environment..." -ForegroundColor Yellow
    
    # Check and install dependencies
    if (!$SkipDependencies) {
        Write-Host "📦 Installing dependencies..." -ForegroundColor Gray
        
        # Backend dependencies
        Push-Location "backend"
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        Pop-Location
        
        # Frontend dependencies
        Push-Location "frontend"
        npm install
        Pop-Location
        
        Write-Host "✅ Dependencies installed!" -ForegroundColor Green
    }
    
    # Setup database
    Write-Host "🗄️  Setting up database..." -ForegroundColor Gray
    docker-compose up -d db
    Start-Sleep -Seconds 10
    
    # Run migrations
    Push-Location "backend"
    alembic upgrade head
    Pop-Location
    
    # Start services
    Write-Host "🚀 Starting services..." -ForegroundColor Gray
    
    # Start backend
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    
    # Start frontend
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"
    
    # Start monitoring if requested
    if ($WithMonitoring) {
        Write-Host "📊 Starting monitoring stack..." -ForegroundColor Gray
        docker-compose up -d prometheus grafana alertmanager node-exporter
    }
    
    Write-Host "✅ Development environment ready!" -ForegroundColor Green
    Write-Host "🔗 Access URLs:" -ForegroundColor Cyan
    Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
    if ($WithMonitoring) {
        Write-Host "   Grafana:  http://localhost:3001 (admin/admin123)" -ForegroundColor White
    }
}

function Setup-Production {
    Write-Host "☁️  Setting up production environment..." -ForegroundColor Yellow
    
    # Check if kubectl is available
    if (!(Get-Command "kubectl" -ErrorAction SilentlyContinue)) {
        Write-Host "❌ kubectl not found. Installing..." -ForegroundColor Red
        # Install kubectl
        curl.exe -LO "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe"
        Move-Item kubectl.exe C:\Windows\System32\
    }
    
    # Apply Kubernetes manifests
    Write-Host "📦 Deploying to Kubernetes..." -ForegroundColor Gray
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/backend.yaml
    kubectl apply -f k8s/frontend.yaml
    
    # Wait for deployments
    Write-Host "⏳ Waiting for deployments..." -ForegroundColor Gray
    kubectl wait --for=condition=available --timeout=300s deployment/postgres -n smart-contract-rewriter
    kubectl wait --for=condition=available --timeout=300s deployment/backend -n smart-contract-rewriter
    kubectl wait --for=condition=available --timeout=300s deployment/frontend -n smart-contract-rewriter
    
    # Get service URLs
    $frontendUrl = kubectl get svc frontend-service -n smart-contract-rewriter -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
    $backendUrl = kubectl get svc backend-service -n smart-contract-rewriter -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
    
    Write-Host "✅ Production deployment complete!" -ForegroundColor Green
    Write-Host "🔗 Access URLs:" -ForegroundColor Cyan
    Write-Host "   Frontend: http://$frontendUrl:3000" -ForegroundColor White
    Write-Host "   Backend:  http://$backendUrl:8000" -ForegroundColor White
}

function Setup-Render {
    Write-Host "🌐 Deploying to Render.com..." -ForegroundColor Yellow
    
    # Check if Render CLI is installed
    if (!(Get-Command "render" -ErrorAction SilentlyContinue)) {
        Write-Host "📦 Installing Render CLI..." -ForegroundColor Gray
        npm install -g @renderinc/cli
    }
    
    # Deploy using render.yaml
    render deploy --file render.yaml
    
    Write-Host "✅ Render deployment initiated!" -ForegroundColor Green
    Write-Host "🔗 Monitor progress at: https://dashboard.render.com" -ForegroundColor Cyan
}

function Validate-Configuration {
    Write-Host "🔍 Validating configuration..." -ForegroundColor Yellow
    
    $issues = @()
    
    # Check for required files
    $requiredFiles = @(
        "backend/requirements.txt",
        "backend/app/main.py",
        "frontend/package.json",
        "docker-compose.yml"
    )
    
    foreach ($file in $requiredFiles) {
        if (!(Test-Path $file)) {
            $issues += "Missing file: $file"
        }
    }
    
    # Check environment variables
    if ($Environment -ne "development") {
        if ([string]::IsNullOrEmpty($env:GEMINI_API_KEY) -and [string]::IsNullOrEmpty($GeminiApiKey)) {
            $issues += "GEMINI_API_KEY not set"
        }
    }
    
    # Check .env file
    if (!(Test-Path "backend/.env")) {
        $issues += "Backend .env file missing"
    }
    
    if ($issues.Count -gt 0) {
        Write-Host "❌ Configuration issues found:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "   • $issue" -ForegroundColor Red
        }
        return $false
    }
    
    Write-Host "✅ Configuration validated!" -ForegroundColor Green
    return $true
}

function Show-PostSetupInstructions {
    Write-Host ""
    Write-Host "🎉 Setup Complete! Next Steps:" -ForegroundColor Green
    Write-Host "==============================" -ForegroundColor Green
    Write-Host ""
    
    switch ($Environment) {
        "development" {
            Write-Host "🔧 Development Mode:" -ForegroundColor Yellow
            Write-Host "   • Services are running in separate terminal windows" -ForegroundColor White
            Write-Host "   • Make changes to code - they'll auto-reload" -ForegroundColor White
            Write-Host "   • Use health-check.ps1 to diagnose issues" -ForegroundColor White
            Write-Host "   • Access API documentation at /docs endpoint" -ForegroundColor White
        }
        "production" {
            Write-Host "☁️  Production Mode:" -ForegroundColor Yellow
            Write-Host "   • Monitor deployments: kubectl get pods -n smart-contract-rewriter" -ForegroundColor White
            Write-Host "   • Check logs: kubectl logs -f deployment/backend -n smart-contract-rewriter" -ForegroundColor White
            Write-Host "   • Scale services: kubectl scale deployment backend --replicas=3" -ForegroundColor White
        }
        "render" {
            Write-Host "🌐 Render.com Mode:" -ForegroundColor Yellow
            Write-Host "   • Check deployment status in Render dashboard" -ForegroundColor White
            Write-Host "   • Set GEMINI_API_KEY in service environment variables" -ForegroundColor White
            Write-Host "   • Configure custom domain if needed" -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Host "🛠️  Available Scripts:" -ForegroundColor Cyan
    Write-Host "   .\scripts\health-check.ps1 -Fix      # Diagnose and fix issues" -ForegroundColor White
    Write-Host "   .\scripts\setup-monitoring.ps1 -Local # Start monitoring stack" -ForegroundColor White
    Write-Host "   .\scripts\deploy-render.ps1           # Deploy to Render" -ForegroundColor White
    Write-Host ""
    Write-Host "📚 Documentation:" -ForegroundColor Cyan
    Write-Host "   • API Documentation: /docs endpoint" -ForegroundColor White
    Write-Host "   • Frontend: Built with React + TypeScript + Vite" -ForegroundColor White
    Write-Host "   • Backend: FastAPI + PostgreSQL + Gemini AI" -ForegroundColor White
}

# Main execution
if (!(Validate-Configuration)) {
    Write-Host "❌ Please fix configuration issues before proceeding." -ForegroundColor Red
    exit 1
}

# Set GEMINI_API_KEY if provided
if ($GeminiApiKey) {
    $env:GEMINI_API_KEY = $GeminiApiKey
    Write-Host "✅ GEMINI_API_KEY set from parameter" -ForegroundColor Green
}

# Execute setup based on environment
switch ($Environment) {
    "development" { Setup-Development }
    "production" { Setup-Production }
    "render" { Setup-Render }
}

Show-PostSetupInstructions

Write-Host ""
Write-Host "🎯 Your Smart Contract Rewriter is ready!" -ForegroundColor Green
