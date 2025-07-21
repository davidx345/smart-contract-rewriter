# SoliVolt (Enterprise Smart Contract Platform) 🚀

AI-powered enterprise platform for analyzing, rewriting, optimizing, and enhancing smart contract security using advanced LLMs and Web3 technologies. Built with comprehensive authentication, user management, and enterprise-grade security features.

## 🌟 Key Features

### 🔐 **Enterprise Authentication & Security**
- **JWT-based Authentication**: Secure token-based auth with refresh tokens
- **Role-Based Access Control (RBAC)**: User, Premium, Enterprise, Admin roles
- **OAuth Integration**: Google, GitHub, LinkedIn sign-in
- **Account Security**: Password strength validation, account lockout, session management
- **Audit Logging**: Comprehensive activity tracking and security monitoring
- **Rate Limiting**: API protection with configurable rate limits

### 🤖 **AI-Powered Smart Contract Tools**
- **Intelligent Analysis**: Leverage Google Gemini AI for deep contract analysis
- **Automated Rewriting**: Contract optimization and enhancement
- **Security Vulnerability Detection**: Identify and fix security issues
- **Gas Optimization**: Reduce costs and improve efficiency
- **Code Generation**: AI-assisted smart contract creation

### 📊 **Enterprise Management**
- **User Dashboard**: Comprehensive analytics and usage statistics
- **Contract History**: Track all analyses and generations
- **Team Management**: Enterprise user and role management
- **API Analytics**: Usage tracking and performance metrics

### 🚨 **Monitoring & DevOps**
- **Real-time Monitoring**: Grafana and Prometheus integration
- **Smart Alerting**: Slack and email notifications
- **Health Checks**: Comprehensive system health monitoring
- **Cloud Deployment**: Kubernetes and Render.com ready

## 🏗️ Enterprise Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend│    │  PostgreSQL DB  │
│  (TypeScript +  │◄──►│  (Python +      │◄──►│  (Auth + Data)  │
│   Auth Context) │    │   JWT/RBAC)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
    ┌────────────┐      ┌─────────────────┐    ┌─────────────────┐
    │OAuth Providers│    │   Gemini AI     │    │   Redis Cache   │
    │(Google/GitHub/│    │   (Analysis)    │    │ (Sessions/Rate  │
    │  LinkedIn)   │    │                 │    │   Limiting)     │
    └────────────┘      └─────────────────┘    └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   Monitoring    │
                        │ (Prometheus +   │
                        │   Grafana)      │
                        └─────────────────┘
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```powershell
# Clone and navigate to project
git clone <your-repo>
cd solivolt

# Run master setup script with authentication
.\scripts\master-setup.ps1 -Environment development -WithMonitoring -WithAuth

# Or for production
.\scripts\master-setup.ps1 -Environment production -WithAuth

# Or deploy to Render.com
.\scripts\master-setup.ps1 -Environment render -GeminiApiKey "your_api_key"
```

### Option 2: Manual Setup

#### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

#### 1. Setup Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Setup database
docker-compose up -d db
alembic upgrade head

# Start backend
uvicorn app.main:app --reload
```

#### 2. Setup Frontend
```powershell
cd frontend
npm install
npm run dev
```

#### 3. Setup Monitoring (Optional)
```powershell
.\scripts\setup-monitoring.ps1 -Local
```

## 🔧 Configuration

### Environment Variables

Create `backend/.env`:
```env
# Database
DATABASE_URL=postgresql://postgres:password123@localhost:5432/solivolt

# AI Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Security
SECRET_KEY=your_secret_key_here
DEBUG=true

# Web3
WEB3_PROVIDER_URL=https://mainnet.infura.io/v3/demo
ETHEREUM_NETWORK=mainnet

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend Configuration

Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

## 📊 Monitoring & Alerting

### Local Monitoring Stack
```powershell
# Start monitoring
.\scripts\setup-monitoring.ps1 -Local

# Access dashboards
# Grafana:      http://localhost:3001 (admin/admin123)
# Prometheus:   http://localhost:9090
# Alertmanager: http://localhost:9093
```

### Configure Alerts
```powershell
# Setup Slack notifications
.\scripts\setup-monitoring.ps1 -Local -SlackWebhook "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Setup Email notifications
.\scripts\setup-monitoring.ps1 -Local -EmailConfig "smtp.gmail.com:587:user:pass:email@domain.com"
```

### Monitored Metrics
- 🔥 HTTP Request Rate & Response Times
- 💾 CPU & Memory Usage  
- 🗄️ Database Performance
- ❌ Error Rates & Status Codes
- 📝 Smart Contract Processing Metrics
- 💚 System Health & Uptime

## 🚨 Health Monitoring

```powershell
# Run comprehensive health check
.\scripts\health-check.ps1 -Detailed

# Auto-fix common issues
.\scripts\health-check.ps1 -Fix

# Custom health check
.\scripts\health-check.ps1 -BackendUrl "http://localhost:8000" -FrontendUrl "http://localhost:3000"
```

## ☁️ Deployment

### Kubernetes Deployment
```powershell
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n solivolt

# Scale services
kubectl scale deployment backend --replicas=3 -n solivolt
```

### Render.com Deployment
```powershell
# Deploy to Render
.\scripts\deploy-render.ps1

# Or using render.yaml
render deploy --file render.yaml
```

### Docker Compose
```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Scale services
docker-compose up -d --scale backend=3
```

## 🧪 API Documentation

Once running, access interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```http
POST /api/v1/contracts/analyze
POST /api/v1/contracts/rewrite  
GET  /api/v1/contracts/history
GET  /health
GET  /metrics  # Prometheus metrics
```

## 🧪 Testing

```powershell
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests  
cd frontend
npm test

# Integration tests
.\scripts\health-check.ps1 -Detailed
```

## 📁 Project Structure

```
solivolt/
├── 🔧 scripts/                    # Deployment & setup scripts
│   ├── master-setup.ps1           # Master setup script
│   ├── health-check.ps1           # Health monitoring
│   ├── setup-monitoring.ps1       # Monitoring setup
│   └── deploy-render.ps1          # Render deployment
├── 🐳 docker-compose.yml          # Local development stack
├── ☸️ k8s/                        # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── postgres.yaml
│   ├── backend.yaml
│   └── frontend.yaml
├── 📊 monitoring/                 # Monitoring configuration
│   ├── prometheus/                # Prometheus config
│   ├── grafana/                   # Grafana dashboards
│   └── alertmanager/              # Alert configuration
├── 🔙 backend/                    # FastAPI application
│   ├── app/                       # Main application
│   │   ├── apis/v1/              # API routes
│   │   ├── core/                 # Configuration
│   │   ├── db/                   # Database
│   │   ├── models/               # Pydantic models
│   │   ├── schemas/              # SQLAlchemy schemas
│   │   └── services/             # Business logic
│   ├── tests/                    # Backend tests
│   ├── alembic/                  # Database migrations
│   ├── Dockerfile               # Backend container
│   └── requirements.txt         # Python dependencies
├── 🎨 frontend/                   # React TypeScript app
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API services
│   │   ├── hooks/               # Custom hooks
│   │   └── types/               # TypeScript types
│   ├── Dockerfile               # Frontend container
│   └── package.json             # Node dependencies
├── 🌐 render.yaml                # Render.com config
└── 🤖 .github/workflows/         # CI/CD pipeline
    └── ci-cd.yml                # GitHub Actions
```

## 🛠️ Troubleshooting

### Common Issues

#### 🔥 Backend Not Starting
```powershell
# Check database connection
docker-compose up -d db
.\scripts\health-check.ps1 -Fix

# Run migrations
cd backend
alembic upgrade head
```

#### 🎨 Frontend Build Errors
```powershell
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 🗄️ Database Connection Issues
```powershell
# Reset database
docker-compose down -v
docker-compose up -d db
cd backend
alembic upgrade head
```

### Getting Help

1. **Health Check**: Run `.\scripts\health-check.ps1 -Detailed`
2. **Logs**: Check service logs in Docker Compose or Kubernetes
3. **Monitoring**: Use Grafana dashboards for system insights
4. **API Docs**: Visit `/docs` endpoint for API documentation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000  
- **API Docs**: http://localhost:8000/docs
- **Monitoring**: http://localhost:3001
- **Prometheus**: http://localhost:9090

---

**Built with ❤️ using FastAPI, React, PostgreSQL, and Google Gemini AI**
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/           # Simple Web App (HTML, CSS, JS)
│   ├── public/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── .dockerignore
├── docker-compose.yml  # For local development
├── .gitignore
└── README.md
```

## Prerequisites

*   Docker & Docker Compose
*   Python 3.9+ (for local backend development if not using Docker exclusively)
*   Node.js & npm (optional, if you expand frontend tooling)

## Getting Started (Local Development with Docker)

1.  **Clone the repository (if applicable):**
    ```bash
    # git clone <your-repo-url>
    # cd solivolt
    ```

2.  **Create environment files:**
    *   Create `backend/.env` based on `backend/.env.example` (you'll need to create this example file or add variables directly to `docker-compose.yml` for now).
      Example `backend/.env`:
      ```env
      DATABASE_URL=postgresql://user:password@db:5432/smart_contract_db
      # OPENAI_API_KEY=your_openai_api_key_here
      # Add other necessary environment variables
      ```
    *   The `docker-compose.yml` already defines default PostgreSQL credentials. You can override them by setting `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` in your shell environment or a `.env` file at the root of the project (Docker Compose automatically picks it up).

3.  **Build and run the services using Docker Compose:**
    ```powershell
    docker-compose up --build
    ```
    *   This will build the Docker images for the backend and frontend, and start the backend server, frontend server (Nginx), and PostgreSQL database.

4.  **Access the services:**
    *   **Backend API:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) (Swagger UI)
    *   **Frontend Web App:** [http://localhost:8080](http://localhost:8080)

## Backend Development (without Docker, if preferred for quick iteration)

1.  Navigate to the `backend` directory:
    ```powershell
    cd backend
    ```
2.  Create a virtual environment:
    ```powershell
    python -m venv .venv
    .".venv\Scripts\Activate.ps1" # For PowerShell
    # source .venv/bin/activate # For bash/zsh
    ```
3.  Install dependencies:
    ```powershell
    pip install -r requirements.txt
    ```
4.  Set up your `.env` file in the `backend` directory as described above.
5.  Run the FastAPI development server:
    ```powershell
    uvicorn app.main:app --reload --port 8000
    ```

## Running Tests (Backend)

1.  Ensure you are in the `backend` directory with the virtual environment activated.
2.  Install test dependencies (if not already included in `requirements.txt`):
    ```powershell
    pip install pytest httpx
    ```
3.  Run pytest:
    ```powershell
    pytest
    ```

## Next Steps

*   Implement the actual LLM integration in `backend/app/services/contract_processing_service.py`.
*   Connect the FastAPI backend to the PostgreSQL database (uncomment and configure `backend/app/db/session.py` and `backend/app/schemas/`).
*   Implement user authentication if needed.
*   Expand frontend features and styling.
*   Set up CI/CD pipelines for deployment.
*   Refine Dockerfiles for production builds (multi-stage builds, smaller images).

