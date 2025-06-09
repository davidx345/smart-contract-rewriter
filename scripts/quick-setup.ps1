# Quick Setup Script for Smart Contract Rewriter
Write-Host "Smart Contract Rewriter - Quick Setup" -ForegroundColor Green

# Navigate to project root
$ProjectRoot = "C:\Users\david\Documents\projects\smart_contract_rewriter"
Set-Location $ProjectRoot

# Step 1: Create environment files
Write-Host "Creating environment files..." -ForegroundColor Yellow

# Backend .env
$BackendEnv = @"
DATABASE_URL=postgresql://postgres:260307@localhost:5432/smart_contract_rewriter
GEMINI_API_KEY=AIzaSyAvTTNwteoYU_4eFG4_2NjnbERAEANBLRs
SECRET_KEY=2wsdn73ge8n28h748nwinfbc7f4
DEBUG=true
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000
APP_NAME=Smart Contract Rewriter
APP_VERSION=1.0.0
PROMETHEUS_ENABLED=true
METRICS_PORT=8001
"@

Set-Content -Path "backend\.env" -Value $BackendEnv
Write-Host "Created backend .env" -ForegroundColor Green

# Frontend .env
$FrontendEnv = @"
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Smart Contract Rewriter
VITE_APP_VERSION=1.0.0
"@

Set-Content -Path "frontend\.env" -Value $FrontendEnv
Write-Host "Created frontend .env" -ForegroundColor Green

# Step 2: Install Python dependencies
Write-Host "📦 Installing backend dependencies..." -ForegroundColor Yellow
Set-Location "backend"
pip install -r requirements.txt
Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
Set-Location ".."

# Step 3: Install Node dependencies
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location "frontend"
npm install
Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
Set-Location ".."

# Step 4: Start services
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
Set-Location $ProjectRoot
docker-compose up -d postgres

# Wait for database
Write-Host "⏳ Waiting for database to start..." -ForegroundColor Yellow
Start-Sleep 10

# Run migrations
Write-Host "🔄 Running database migrations..." -ForegroundColor Yellow
Set-Location "backend"
alembic upgrade head
Write-Host "✅ Database migrations completed" -ForegroundColor Green

Set-Location $ProjectRoot
Write-Host "🎉 Quick setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: docker-compose up -d" -ForegroundColor White
Write-Host "2. Visit: http://localhost:3000" -ForegroundColor White
