#!/bin/bash

# Smart Contract Rewriter - Render.com Deployment Script

set -e

echo "🚀 Starting deployment to Render.com..."

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    echo "❌ Render CLI not found. Installing..."
    npm install -g @renderinc/cli
fi

# Login check
echo "🔐 Checking Render authentication..."
if ! render auth whoami &> /dev/null; then
    echo "❌ Not logged in to Render. Please run: render auth login"
    exit 1
fi

# Validate environment variables
echo "🔍 Validating environment variables..."
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY not set. You'll need to set this in Render dashboard."
fi

# Deploy services
echo "📦 Deploying services to Render..."

# Deploy database first
echo "🗄️  Creating database service..."
render services create --type pserv --name smart-contract-db --plan starter

# Deploy backend
echo "🔧 Deploying backend service..."
render services create --type web --name smart-contract-backend --plan starter \
    --dockerfile ./backend/Dockerfile \
    --docker-context ./backend \
    --health-check-path /health

# Deploy frontend
echo "🌐 Deploying frontend service..."
render services create --type web --name smart-contract-frontend --plan starter \
    --env static \
    --build-command "cd frontend && npm ci && npm run build" \
    --publish-path "frontend/dist"

echo "✅ Deployment initiated! Check your Render dashboard for progress."
echo "🔗 Services will be available at:"
echo "   Frontend: https://smart-contract-frontend.onrender.com"
echo "   Backend:  https://smart-contract-backend.onrender.com"
echo ""
echo "⚠️  Don't forget to:"
echo "   1. Set GEMINI_API_KEY in backend service environment variables"
echo "   2. Update CORS origins in backend if needed"
echo "   3. Configure custom domain if desired"
