# Smart Contract Rewriter - Render.com Deployment Script (PowerShell)

param(
    [switch]$SkipAuth,
    [string]$GeminiApiKey
)

Write-Host "🚀 Starting deployment to Render.com..." -ForegroundColor Green

# Check if Render CLI is installed
if (!(Get-Command "render" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Render CLI not found. Installing..." -ForegroundColor Red
    npm install -g @renderinc/cli
}

# Login check
if (!$SkipAuth) {
    Write-Host "🔐 Checking Render authentication..." -ForegroundColor Yellow
    $authCheck = render auth whoami 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Not logged in to Render. Please run: render auth login" -ForegroundColor Red
        exit 1
    }
}

# Validate environment variables
Write-Host "🔍 Validating environment variables..." -ForegroundColor Yellow
if ([string]::IsNullOrEmpty($env:GEMINI_API_KEY) -and [string]::IsNullOrEmpty($GeminiApiKey)) {
    Write-Host "⚠️  Warning: GEMINI_API_KEY not set. You'll need to set this in Render dashboard." -ForegroundColor Yellow
}

# Check if render.yaml exists
if (!(Test-Path "render.yaml")) {
    Write-Host "❌ render.yaml not found in current directory!" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Deploying services using render.yaml..." -ForegroundColor Green

# Deploy using render.yaml
try {
    render deploy --file render.yaml
    Write-Host "✅ Deployment initiated successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔗 Services will be available at:" -ForegroundColor Cyan
Write-Host "   Frontend: https://smart-contract-frontend.onrender.com" -ForegroundColor White
Write-Host "   Backend:  https://smart-contract-backend.onrender.com" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Don't forget to:" -ForegroundColor Yellow
Write-Host "   1. Set GEMINI_API_KEY in backend service environment variables" -ForegroundColor White
Write-Host "   2. Update CORS origins in backend if needed" -ForegroundColor White
Write-Host "   3. Configure custom domain if desired" -ForegroundColor White
Write-Host "   4. Monitor deployment progress in Render dashboard" -ForegroundColor White
