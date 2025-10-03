# 🚀 Complete Setup Guide

## 📋 **Quick Navigation**

- [🎯 Prerequisites](#-prerequisites)
- [⚡ Quick Start (5 minutes)](#-quick-start-5-minutes)
- [🛠️ Local Development Setup](#️-local-development-setup)
- [🐳 Docker Development](#-docker-development)
- [☁️ AWS Deployment](#️-aws-deployment)
- [📊 Monitoring Setup](#-monitoring-setup)
- [🧪 Testing](#-testing)
- [🔧 Troubleshooting](#-troubleshooting)

---

## 🎯 **Prerequisites**

### **💻 Required Software**

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| **Python** | 3.11+ | Backend services | [Download](https://python.org/downloads/) |
| **Node.js** | 18+ | Frontend development | [Download](https://nodejs.org/) |
| **Docker** | 20+ | Containerization | [Download](https://docker.com/get-started) |
| **Git** | Latest | Version control | [Download](https://git-scm.com/) |
| **AWS CLI** | v2 | Cloud deployment | [Install Guide](https://aws.amazon.com/cli/) |

### **☁️ Required Accounts**
- **AWS Account** - For cloud infrastructure
- **Google Cloud** - For Gemini AI API
- **Slack** (optional) - For notifications
- **GitHub** - For CI/CD and OAuth

### **🔐 Required API Keys**
- **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **AWS Access Keys** - From AWS Console IAM
- **Slack Webhook** (optional) - From Slack App configuration

---

## ⚡ **Quick Start (5 minutes)**

### **🚀 Option 1: Docker Compose (Recommended)**

```bash
# 1. Clone the repository
git clone https://github.com/davidx345/smart-contract-rewriter.git
cd smart-contract-rewriter

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your API keys
nano .env  # or your preferred editor

# 4. Start all services
docker-compose up -d

# 5. Wait for services to start (30-60 seconds)
docker-compose logs -f

# 6. Access the application
open http://localhost:3000    # Frontend
open http://localhost:8000/docs  # API Documentation
```

### **🌐 Service URLs**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Monitoring**: http://localhost:3001 (if enabled)

---

## 🛠️ **Local Development Setup**

### **🐍 Backend Setup**

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database (PostgreSQL required)
# Option 1: Use Docker for database only
docker-compose up -d db

# Option 2: Use local PostgreSQL
# Install PostgreSQL locally and create database

# Configure environment
cp .env.example .env
# Edit .env with your database URL and API keys

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **⚛️ Frontend Setup**

```bash
# Navigate to frontend directory (new terminal)
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with backend URL

# Start development server
npm run dev

# Application will be available at http://localhost:3000
```

### **🗄️ Database Setup Options**

#### **Option A: Docker PostgreSQL (Recommended)**
```bash
# Start PostgreSQL container
docker-compose up -d db

# Database will be available at:
# Host: localhost
# Port: 5432
# Database: smart_contract_db
# Username: postgres
# Password: password123
```

#### **Option B: Local PostgreSQL**
```bash
# Install PostgreSQL locally
# Create database
createdb smart_contract_db

# Update .env with your local database URL
DATABASE_URL=postgresql://username:password@localhost:5432/smart_contract_db
```

---

## 🐳 **Docker Development**

### **🔧 Full Stack with Docker**

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Clean up volumes (removes database data)
docker-compose down -v
```

### **🏗️ Individual Service Development**

```bash
# Backend only
docker-compose up -d db
docker-compose up backend

# Frontend only  
docker-compose up frontend

# Database only
docker-compose up -d db
```

### **🔧 Docker Troubleshooting**

```bash
# Rebuild images without cache
docker-compose build --no-cache

# View container status
docker-compose ps

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Check container logs
docker-compose logs backend
docker-compose logs frontend

# Restart specific service
docker-compose restart backend
```

---

## ☁️ **AWS Deployment**

### **🚀 Infrastructure Setup**

#### **Prerequisites**
```bash
# Configure AWS CLI
aws configure

# Install Terraform (optional for IaC)
# Download from https://terraform.io/downloads/

# Install kubectl for Kubernetes
# Download from https://kubernetes.io/docs/tasks/tools/
```

#### **Manual AWS Setup**

1. **VPC and Networking**
```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b
```

2. **Database Setup**
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier smart-contract-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password your-password \
  --allocated-storage 20
```

3. **Application Deployment**
```bash
# Create EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxx \
  --subnet-id subnet-xxx
```

### **🐳 Container Deployment**

```bash
# Build and push Docker images
docker build -t smart-contract-backend ./backend
docker build -t smart-contract-frontend ./frontend

# Tag for ECR
docker tag smart-contract-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/smart-contract-backend:latest
docker tag smart-contract-frontend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/smart-contract-frontend:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/smart-contract-backend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/smart-contract-frontend:latest
```

### **☸️ Kubernetes Deployment**

```bash
# Create namespace
kubectl create namespace smart-contract-platform

# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n smart-contract-platform

# Access application
kubectl port-forward service/frontend 3000:80 -n smart-contract-platform
```

---

## 📊 **Monitoring Setup**

### **🔧 Local Monitoring Stack**

```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Or include in main compose
docker-compose up -d

# Access monitoring dashboards
open http://localhost:3001  # Grafana (admin/admin123)
open http://localhost:9090  # Prometheus
open http://localhost:9093  # Alertmanager
```

### **📈 Configure Dashboards**

1. **Grafana Setup**
```bash
# Import pre-built dashboards
curl -X POST \
  http://admin:admin123@localhost:3001/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana/dashboards/smart-contract-dashboard.json
```

2. **Prometheus Configuration**
```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'smart-contract-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    
  - job_name: 'smart-contract-frontend'
    static_configs:
      - targets: ['frontend:80']
```

### **🚨 Alerting Setup**

```bash
# Configure Slack notifications
# Edit monitoring/alertmanager/alertmanager.yml
# Add your Slack webhook URL

# Test alerts
curl -XPOST http://localhost:9093/api/v1/alerts -H 'Content-Type: application/json' -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "Test alert for setup verification"
    }
  }
]'
```

---

## 🧪 **Testing**

### **🐍 Backend Testing**

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_contract_endpoints.py

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html
```

### **⚛️ Frontend Testing**

```bash
cd frontend

# Run unit tests
npm test

# Run tests with coverage
npm run test:coverage

# Run E2E tests (requires running backend)
npm run test:e2e

# Run tests in watch mode
npm run test:watch
```

### **🔧 Integration Testing**

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Load testing
npm install -g artillery
artillery run tests/load/load-test.yml
```

### **🚀 API Testing**

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/contracts/analyze \
  -H "Content-Type: application/json" \
  -d '{"source_code": "pragma solidity ^0.8.0; contract Test {}"}'

# Using httpie
http POST localhost:8000/api/v1/contracts/analyze \
  source_code="pragma solidity ^0.8.0; contract Test {}"

# Using Postman
# Import the collection from docs/postman/smart-contract-api.json
```

---

## 🔧 **Troubleshooting**

### **🐛 Common Issues & Solutions**

#### **Backend Won't Start**

```bash
# Check Python version
python --version  # Should be 3.11+

# Check virtual environment
which python  # Should point to .venv

# Check dependencies
pip list

# Check database connection
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:password123@localhost:5432/smart_contract_db')
print('Database connection successful')
"

# Check environment variables
python -c "
from app.core.config import settings
print(f'Database URL: {settings.DATABASE_URL}')
print(f'Gemini API Key configured: {bool(settings.GEMINI_API_KEY)}')
"
```

#### **Frontend Won't Start**

```bash
# Check Node.js version
node --version  # Should be 18+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check backend connection
curl http://localhost:8000/health

# Check environment variables
cat .env.local
```

#### **Database Connection Issues**

```bash
# Check PostgreSQL is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test database connection
docker-compose exec db psql -U postgres -d smart_contract_db -c "SELECT version();"

# Reset database
docker-compose down -v
docker-compose up -d db
# Wait 30 seconds for startup
cd backend && alembic upgrade head
```

#### **Docker Issues**

```bash
# Check Docker is running
docker ps

# Check disk space
docker system df

# Clean up Docker
docker system prune -a

# Rebuild images
docker-compose build --no-cache

# Check container logs
docker-compose logs -f backend
```

### **🔍 Debug Mode**

```bash
# Backend debug mode
cd backend
export DEBUG=true
uvicorn app.main:app --reload --log-level debug

# Frontend debug mode
cd frontend
npm run dev -- --debug

# Docker debug mode
docker-compose -f docker-compose.debug.yml up
```

### **📊 Health Checks**

```bash
# Backend health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Full system health
curl http://localhost:8000/health/full

# Monitoring health
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3001/api/health  # Grafana
```

### **🚨 Emergency Procedures**

#### **Application Recovery**
```bash
# Quick restart
docker-compose restart

# Full reset (loses data)
docker-compose down -v
docker-compose up -d

# Rollback to previous version
git checkout HEAD~1
docker-compose up --build -d
```

#### **Data Recovery**
```bash
# Backup database
docker-compose exec db pg_dump -U postgres smart_contract_db > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres smart_contract_db < backup.sql
```

---

## 📞 **Getting Help**

### **📚 Resources**
- **Documentation**: [docs/](docs/)
- **API Reference**: http://localhost:8000/docs
- **Architecture Guide**: [docs/architecture.md](docs/architecture.md)
- **Security Guide**: [docs/security.md](docs/security.md)

### **🐛 Issue Reporting**
1. Check [troubleshooting section](#-troubleshooting)
2. Check existing GitHub issues
3. Provide detailed error logs
4. Include environment information

### **💬 Community**
- **GitHub Issues**: Technical problems
- **GitHub Discussions**: General questions
- **Stack Overflow**: Tag `smart-contract-rewriter`

---

<div align="center">

**🎉 Congratulations! Your Smart Contract Platform is ready!**

**Next Steps:**
- 🚀 [Deploy to production](docs/deployment.md)
- 📊 [Set up monitoring](docs/monitoring.md)
- 🔐 [Review security](docs/security.md)
- 🤝 [Contribute to the project](CONTRIBUTING.md)

</div>