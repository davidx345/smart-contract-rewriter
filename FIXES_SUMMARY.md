# Smart Contract Rewriter - Quick Setup Guide

## 🚀 Fixed Issues

### ✅ Backend Fixes
1. **Added Delete Endpoint**: `/api/v1/contracts/history/{contract_id}` - DELETE
2. **Improved History Data**: Enhanced contract history with proper gas savings, vulnerability counts, and optimization metrics
3. **Better Error Handling**: Improved error responses and validation

### ✅ Frontend Fixes  
1. **Real Metrics Display**: Gas savings, issues count, and optimizations now show actual values instead of zeros
2. **Working Delete Button**: Users can now delete contracts from history
3. **Download Functionality**: Download original and optimized contract code
4. **Better Data Extraction**: Improved parsing of backend response data

## 🔧 Quick Start

### 1. Backend Setup (Terminal 1)
```powershell
cd backend
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup (Terminal 2)
```powershell
cd frontend
# Install dependencies
npm install

# Start frontend
npm run dev
```

### 3. Database Setup (Terminal 3)
```powershell
# Start PostgreSQL with Docker
docker-compose up -d db

# Run migrations
cd backend
alembic upgrade head
```

## 🧪 Test the Fixes

1. **Visit**: http://localhost:3000
2. **Analyze a Contract**: Paste a Solidity contract and click "Analyze"
3. **Check History**: Go to Contract History page
4. **Verify Metrics**: You should now see real numbers for:
   - Gas Saved percentage
   - Issues count (vulnerabilities found)
   - Optimizations count
5. **Test Delete**: Click the trash icon to delete a contract
6. **Test Download**: Click download buttons for original/optimized code

## 🐛 Common Issues

### Backend Not Starting
- Check if PostgreSQL is running: `docker-compose up -d db`
- Verify GEMINI_API_KEY is set in backend/.env
- Check port 8000 is not in use

### Frontend Build Errors
- Run: `npm install` to ensure all dependencies are installed
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

### Database Connection Issues  
- Ensure PostgreSQL is running on port 5432
- Check DATABASE_URL in backend/.env
- Run: `alembic upgrade head` to apply migrations

## 📊 Data Flow

1. **Contract Analysis/Rewrite** → Stored in PostgreSQL
2. **History API** → Returns enriched data with metrics
3. **Frontend** → Extracts and displays real metrics
4. **Delete API** → Removes contracts from both analysis and rewrite tables

## 🔍 API Endpoints

- `GET /api/v1/contracts/history` - List contract history with metrics
- `DELETE /api/v1/contracts/history/{id}` - Delete contract from history
- `GET /api/v1/contracts/history/{id}` - Get specific contract details
- `POST /api/v1/contracts/analyze` - Analyze contract
- `POST /api/v1/contracts/rewrite` - Rewrite/optimize contract

## 📈 Key Improvements

### Backend
- Enhanced `ContractHistoryResponse` model with detailed metrics
- Added proper gas savings calculation from Gemini AI responses
- Better error handling and validation
- Comprehensive delete functionality

### Frontend  
- Fixed `getOptimizationSummary()` to read from correct data fields
- Improved API response mapping in `apiService.getContractHistory()`
- Added real download functionality for contract files
- Better TypeScript configuration for development
