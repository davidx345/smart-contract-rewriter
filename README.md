# Smart Contract Rewriter & Analyzer Platform

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)
[![AWS](https://img.shields.io/badge/AWS-Cloud%20Infrastructure-orange.svg)](https://aws.amazon.com)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue.svg)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestrated-326CE5.svg)](https://kubernetes.io)

An enterprise-grade, cloud-native platform for AI-powered smart contract analysis, security auditing, and automated optimization. Built with modern DevOps practices including containerization, orchestration, infrastructure-as-code, and comprehensive monitoring.

---

## Project Overview

The Smart Contract Rewriter Platform is a production-ready SaaS application that leverages AI to analyze, audit, and optimize Solidity smart contracts. The platform identifies security vulnerabilities, provides gas optimization recommendations, and generates rewritten contracts following industry best practices.

### Problem Statement

Smart contract development requires specialized security knowledge and optimization expertise. Manual code reviews are time-consuming, inconsistent, and error-prone. This platform addresses these challenges by providing:

- Automated security vulnerability detection
- AI-powered code optimization recommendations
- Gas consumption analysis and reduction strategies
- Contract generation from natural language descriptions
- Historical analysis tracking and comparison

### Key Use Cases

- **Security Auditing**: Identify reentrancy vulnerabilities, access control issues, and common attack vectors
- **Gas Optimization**: Reduce transaction costs through storage pattern analysis and algorithmic improvements
- **Code Quality**: Enforce best practices, naming conventions, and industry standards
- **Contract Generation**: Bootstrap new contracts from feature descriptions
- **Educational Tool**: Learn secure contract patterns through automated feedback

---

## Features

### Core Functionality

- **AI-Powered Analysis**: Deep contract inspection using Google Gemini AI with customizable analysis types
- **Security Vulnerability Detection**: Automated identification of critical, high, medium, and low severity issues
- **Gas Optimization**: Per-function gas analysis with specific recommendations for cost reduction
- **Automated Rewriting**: Generate optimized contract versions preserving original functionality
- **Contract Generation**: Create smart contracts from natural language descriptions
- **File Upload Support**: Direct `.sol` file analysis with syntax validation

### Enterprise Capabilities

- **Rate Limiting**: Redis-backed request throttling to prevent abuse
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Historical Tracking**: Contract analysis history with comparison capabilities
- **Alerting**: Slack and email notifications for critical system events
- **Health Checks**: Comprehensive liveness and readiness probes

---

## Architecture

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.11) with async/await patterns
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **Caching**: Redis 7 for session management and rate limiting
- **Blockchain**: Web3.py for Ethereum interaction
- **Testing**: pytest with async support

#### Frontend
- **Framework**: React 19 with TypeScript 5.8
- **Build Tool**: Vite 6.3
- **State Management**: React Context API with custom hooks
- **UI Components**: Tailwind CSS with custom design system
- **Code Editor**: Monaco Editor for syntax highlighting
- **HTTP Client**: Axios with request/response interceptors
- **Form Management**: React Hook Form with validation

#### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes (EKS) with Horizontal Pod Autoscaling
- **Infrastructure as Code**: Terraform with remote state management
- **Load Balancing**: AWS Application Load Balancer with SSL termination
- **Monitoring**: Prometheus + Grafana + Alertmanager stack
- **CI/CD**: GitHub Actions with automated testing and deployment
- **Cloud Providers**: AWS (primary), Azure, DigitalOcean

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet Layer                           │
│  CloudFront CDN ──► Route53 DNS ──► AWS ALB (SSL Termination)  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐       ┌───────▼────────┐
        │   Frontend      │       │   API Gateway  │
        │  (React + Nginx)│       │   (FastAPI)    │
        │  - TypeScript   │       │                │
        │  - Monaco Editor│       │  - Rate Limit  │
        │  - Tailwind CSS │       │  - Validation  │
        └─────────────────┘       └────────┬───────┘
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                  ┌───────▼───────┐  ┌────▼─────┐  ┌──────▼──────┐
                  │ Auth Service   │  │Contract  │  │AI Service   │
                  │ - User Mgmt    │  │Service   │  │- Gemini API │
                  │ - Session Mgmt │  │- Analysis│  │- ML Model   │
                  └───────┬────────┘  │- Rewrite │  └──────┬──────┘
                          │           └────┬─────┘         │
                          └────────────────┼───────────────┘
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                  ┌───────▼────────┐  ┌───▼──────┐  ┌─────▼─────┐
                  │  PostgreSQL RDS │  │  Redis   │  │S3 Storage │
                  │  - User Data    │  │ - Cache  │  │- Contracts│
                  │  - Contracts    │  │ - Session│  │- Backups  │
                  │  - Analytics    │  │ - Queue  │  └───────────┘
                  └─────────────────┘  └──────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    Monitoring & Observability                     │
│  Prometheus ──► Grafana ──► Alertmanager ──► Slack/Email        │
└──────────────────────────────────────────────────────────────────┘
```

### Microservices Architecture

The backend is designed with a microservices approach for scalability:

1. **Unified Main Service** (`unified_main.py`): API gateway handling routing, authentication, and request orchestration
2. **Authentication Service**: User registration, login, JWT token management, session handling
3. **Contract Service**: Smart contract processing, validation, and storage
4. **AI Service** (`ai-service/main.py`): Gemini AI integration for analysis and generation
5. **Notification Service**: Async email and Slack notifications

Each service is independently deployable, scalable, and maintainable.

### Data Flow

1. **User Authentication Flow**:
   - User submits credentials → FastAPI validates → JWT token generated → Redis session created → Token returned to client

2. **Contract Analysis Flow**:
   - User uploads contract → Backend validates Solidity syntax → Sends to AI service → Gemini processes with specialized prompts → Results parsed and formatted → Stored in PostgreSQL → Response returned with vulnerability report

3. **Monitoring Flow**:
   - Application emits metrics → Prometheus scrapes endpoints → Alertmanager evaluates rules → Alerts triggered → Notifications sent → Grafana visualizes trends

---

## Setup and Installation

### Prerequisites

- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.11+ (for local development)
- **Node.js**: 18+ (for frontend development)
- **PostgreSQL**: 15+ (managed by Docker Compose)
- **Redis**: 7+ (managed by Docker Compose)
- **kubectl**: For Kubernetes deployments
- **Terraform**: 1.0+ for infrastructure provisioning

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=solivolt
DATABASE_URL=postgresql://postgres:your_secure_password@db:5432/solivolt

# Redis Configuration
REDIS_PASSWORD=your_redis_password

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_jwt_secret_key_minimum_32_characters

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Authentication
JWT_SECRET_KEY=your_jwt_secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Web3 (Optional)
WEB3_PROVIDER_URL=https://mainnet.infura.io/v3/your_project_id
ETHEREUM_NETWORK=mainnet
```

### Quick Start with Docker Compose

The fastest way to run the entire stack locally:

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-contract-rewriter.git
cd smart-contract-rewriter

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and secrets

# Start all services (backend, frontend, database, redis, monitoring)
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs -f backend

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin123)
```

### Manual Setup for Development

#### Backend Setup

```bash
# Navigate to backend directory
cd microservices

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if using Alembic)
alembic upgrade head

# Start the development server
uvicorn unified_main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure API endpoint
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Start development server
npm run dev

# Build for production
npm run build
```

#### Monitoring Stack Setup

```bash
# Start Prometheus, Grafana, and Alertmanager
docker-compose up -d prometheus grafana alertmanager node-exporter

# Import Grafana dashboards from monitoring/grafana/dashboards/
# Access Grafana at http://localhost:3001
# Default credentials: admin/admin123
```

---

## Configuration

### Backend Configuration

The backend is configured through environment variables and `pyproject.toml`. Key configurations:

- **Database Connection**: PostgreSQL with connection pooling
- **Redis Connection**: For caching and session management
- **CORS Settings**: Configure allowed origins for cross-origin requests
- **Rate Limiting**: Requests per minute per IP address
- **JWT Settings**: Token expiration time and secret key rotation

### Frontend Configuration

Frontend configuration in `frontend/vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### Kubernetes Configuration

Kubernetes manifests in `k8s/` directory:

- **00-namespace.yaml**: Namespace with resource quotas
- **01-configmaps.yaml**: Application configuration
- **02-secrets.yaml**: Sensitive credentials (base64 encoded)
- **06-backend.yaml**: Backend deployment with HPA (2-10 replicas)
- **07-frontend.yaml**: Frontend deployment with HPA (2-5 replicas)
- **11-monitoring.yaml**: Prometheus and Grafana deployment

### Terraform Configuration

Infrastructure defined in `terraform/main.tf`:

- **VPC Module**: Multi-AZ VPC with public/private subnets
- **EC2 Module**: Application servers with security groups
- **RDS Module**: PostgreSQL database with automated backups
- **S3 Buckets**: Application storage with versioning and encryption
- **Remote State**: S3 backend with DynamoDB state locking

---

## Usage Instructions

### API Endpoints

#### Authentication

```bash
# Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
# Returns: {"access_token": "eyJ0eXAi...", "token_type": "bearer"}

# Get current user
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Contract Analysis

```bash
# Analyze contract
curl -X POST http://localhost:8000/contracts/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; contract MyToken { ... }",
    "contract_name": "MyToken"
  }'

# Response format:
{
  "request_id": "req_20250115_103045",
  "original_code": "...",
  "analysis_report": {
    "vulnerabilities": [
      {
        "type": "reentrancy",
        "severity": "high",
        "line_number": 45,
        "description": "Potential reentrancy vulnerability",
        "recommendation": "Use ReentrancyGuard from OpenZeppelin"
      }
    ],
    "gas_analysis_per_function": [...],
    "overall_security_score": 75,
    "general_suggestions": [...]
  },
  "processing_time_seconds": 2.5
}
```

#### Contract Rewriting

```bash
# Rewrite and optimize contract
curl -X POST http://localhost:8000/contracts/rewrite \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0; ...",
    "requirements": "Optimize for gas and add security features"
  }'

# Response includes:
# - rewritten_code: Optimized Solidity code
# - rewrite_report: Specific changes made
# - gas_optimization_details: Before/after gas estimates
```

#### Contract Generation

```bash
# Generate contract from description
curl -X POST http://localhost:8000/contracts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "ERC20 token with voting capabilities",
    "contract_name": "GovernanceToken",
    "features": ["burnable", "pausable", "voting"],
    "compiler_version": "0.8.19"
  }'
```

#### File Upload

```bash
# Upload .sol file for analysis
curl -X POST http://localhost:8000/contracts/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@MyContract.sol"
```

### Web Interface

Access the React frontend at `http://localhost:3000`:

1. **Home Page**: Upload or paste contract code
2. **Analysis View**: Security vulnerabilities with severity indicators
3. **Rewrite View**: Side-by-side comparison of original vs optimized code
4. **Generate View**: Create contracts from natural language
5. **History**: View past analyses and compare results

### Monitoring and Observability

#### Prometheus Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# Response time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active database connections
pg_stat_activity_count

# Redis memory usage
redis_memory_used_bytes
```

#### Grafana Dashboards

Pre-configured dashboards available in `monitoring/grafana/dashboards/`:

- **Application Overview**: Request rate, error rate, latency
- **Infrastructure Metrics**: CPU, memory, disk usage
- **Database Performance**: Connection pool, query time, transactions
- **AI Service Metrics**: Gemini API calls, token usage, response time

#### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health/db

# Redis connectivity
curl http://localhost:8000/health/redis

# Detailed system status
curl http://localhost:8000/health/detailed
```

---

## Folder Structure

```
smart-contract-rewriter/
├── .github/workflows/          # CI/CD pipelines
│   ├── ci-cd.yml              # Backend deployment to AWS EC2
│   ├── frontend-vercel.yml    # Frontend deployment to Vercel
│   └── notifications.yml      # Slack/email notifications
│
├── docs/                       # Comprehensive documentation
│   ├── architecture.md        # System architecture details
│   ├── security.md           # Security implementation
│   ├── setup-guide.md        # Deployment guides
│   └── skills-matrix.md      # Technical competencies
│
├── frontend/                   # React TypeScript application
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Page components (Home, Dashboard)
│   │   ├── services/        # API client (axios)
│   │   ├── contexts/        # React Context providers
│   │   ├── hooks/           # Custom React hooks
│   │   └── types/           # TypeScript type definitions
│   ├── Dockerfile           # Multi-stage production build
│   ├── package.json         # Dependencies and scripts
│   └── vite.config.ts       # Vite build configuration
│
├── microservices/              # Backend services
│   ├── unified_main.py        # Main API gateway and orchestrator
│   ├── ai-service/           # AI analysis microservice
│   │   ├── main.py          # Gemini AI integration
│   │   └── ml_vulnerability_detector.py
│   ├── auth-service/         # Authentication microservice
│   ├── contract-service/     # Contract processing
│   ├── notification-service/ # Email/Slack notifications
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile.unified    # Backend container image
│
├── k8s/                        # Kubernetes manifests (Phase 6)
│   ├── 00-namespace.yaml     # Namespace with quotas
│   ├── 01-configmaps.yaml    # Configuration
│   ├── 02-secrets.yaml       # Sensitive data
│   ├── 04-postgres.yaml      # Database StatefulSet
│   ├── 05-redis.yaml         # Cache deployment
│   ├── 06-backend.yaml       # Backend with HPA (2-10 replicas)
│   ├── 07-frontend.yaml      # Frontend with HPA (2-5 replicas)
│   ├── 08-ingress-networking.yaml # ALB ingress + network policies
│   ├── 09-rbac.yaml          # Role-based access control
│   ├── 11-monitoring.yaml    # Prometheus stack
│   └── deploy.sh             # Automated deployment script
│
├── terraform/                  # Infrastructure as Code (Phase 5)
│   ├── main.tf               # Main configuration
│   ├── modules/
│   │   ├── vpc/             # VPC with multi-AZ subnets
│   │   ├── ec2/             # Application servers
│   │   ├── rds/             # PostgreSQL database
│   │   └── s3/              # Object storage
│   ├── environments/        # Dev/staging/prod configs
│   ├── bootstrap/           # S3 backend setup
│   └── variables.tf         # Input variables
│
├── monitoring/                 # Observability stack
│   ├── prometheus/
│   │   ├── prometheus.yml   # Scrape configuration
│   │   └── alert_rules.yml  # Alerting rules
│   ├── grafana/
│   │   └── dashboards/      # Pre-built dashboards
│   └── alertmanager/
│       └── alertmanager.yml # Notification routing
│
├── tests/                      # Test suites
│   ├── unit/                # Unit tests (pytest)
│   ├── integration/         # Integration tests
│   └── conftest.py          # Test configuration
│
├── docker-compose.yml          # Local development stack
├── requirements.txt            # Root Python dependencies
├── pyproject.toml             # Python project metadata
├── vercel.json                # Vercel deployment config
├── init.sql                   # Database initialization
├── roadmap.md                 # DevOps learning roadmap
└── README.md                  # This file
```

---

## Testing

### Unit Tests

```bash
# Backend tests
cd microservices
pytest tests/unit/ -v --cov=. --cov-report=html

# Frontend tests
cd frontend
npm run test
npm run test:coverage
```

### Integration Tests

```bash
# Full integration test suite
pytest tests/integration/ -v

# Test specific service
pytest tests/integration/test_contract_analysis.py -v
```

### End-to-End Tests

```bash
# Start services
docker-compose up -d

# Run E2E tests
npm run test:e2e

# Health check script
./scripts/health-check.sh
```

---

## Deployment

### Local Development

```bash
docker-compose up -d
```

### AWS EC2 Deployment

Automated via GitHub Actions on push to `main`:

1. Build Docker images
2. Push to GitHub Container Registry
3. SSH to EC2 instance
4. Pull latest images
5. Update containers with zero-downtime rolling deployment
6. Run health checks
7. Send Slack notification

Manual deployment:

```bash
# SSH to EC2
ssh -i your-key.pem ec2-user@your-ec2-ip

# Pull and restart
cd ~/smart-contract-rewriter
git pull origin main
docker-compose up -d --build
```

### Kubernetes Deployment

```bash
# Navigate to k8s directory
cd k8s

# Deploy all components
./deploy.sh deploy

# Check status
kubectl get pods -n smart-contract-rewriter

# Scale backend
kubectl scale deployment backend --replicas=5 -n smart-contract-rewriter

# Monitor rollout
kubectl rollout status deployment/backend -n smart-contract-rewriter
```

### Terraform Infrastructure Provisioning

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan infrastructure changes
terraform plan -var-file="environments/production.tfvars"

# Apply changes
terraform apply -var-file="environments/production.tfvars"

# Outputs (RDS endpoint, VPC ID, etc.)
terraform output
```

### Vercel Frontend Deployment

Automated via `frontend-vercel.yml` workflow:

```bash
# Manual deployment
cd frontend
npm run build
vercel --prod
```

---

## DevOps Competencies Demonstrated

This project showcases enterprise-level DevOps skills across multiple phases:

### Phase 1: Core Foundations ✅
- **Linux Administration**: Process management, systemd services, user permissions
- **Git Workflows**: Feature branching, pull requests, semantic versioning
- **Python Scripting**: Automation scripts for deployment and health checks
- **Cloud Basics**: AWS account setup, IAM policies, billing alerts
- **Networking**: VPC configuration, security groups, load balancing

### Phase 2: Containers & Cloud Compute ✅
- **Docker**: Multi-stage builds, layer optimization, security scanning
- **Docker Compose**: Multi-service orchestration with health checks
- **Cloud VMs**: EC2 provisioning, instance types, security hardening
- **Container Registry**: GitHub Container Registry integration
- **Image Optimization**: Alpine base images, non-root users, minimal layers

### Phase 3: CI/CD Pipelines ✅
- **GitHub Actions**: Multi-stage workflows with job dependencies
- **Automated Testing**: Unit, integration, and security tests in pipeline
- **Security Scanning**: Trivy, Bandit, Safety vulnerability detection
- **Deployment Automation**: Zero-downtime rolling deployments
- **Rollback Strategy**: Automated rollback on deployment failure

### Phase 4: Cloud Storage, Databases & Networking ✅
- **RDS**: PostgreSQL with automated backups, read replicas, encryption
- **S3**: Object storage with lifecycle policies, versioning, encryption
- **VPC Design**: Multi-AZ architecture, public/private subnets, NAT gateways
- **Network Security**: Security groups, NACLs, bastion hosts
- **Database Migration**: Alembic migrations with zero downtime

### Phase 5: Infrastructure as Code ✅
- **Terraform**: Modular infrastructure with remote state management
- **State Management**: S3 backend with DynamoDB locking
- **Resource Tagging**: Cost allocation and resource tracking
- **Security Scanning**: tfsec and Checkov for IaC security
- **Multi-Environment**: Dev/staging/prod configuration separation

### Phase 6: Kubernetes & Orchestration ✅
- **Container Orchestration**: Kubernetes deployments with StatefulSets
- **Auto-scaling**: HPA based on CPU/memory with custom metrics
- **Service Discovery**: DNS-based service communication
- **Network Policies**: Micro-segmentation and zero-trust networking
- **RBAC**: Role-based access control with least privilege
- **Monitoring Integration**: Prometheus ServiceMonitors and alerts
- **Persistent Storage**: PVCs for stateful services
- **Rolling Updates**: Zero-downtime deployments with health checks

---

## Monitoring and Observability

### Metrics Collected

- **Application Metrics**: Request rate, error rate, latency (p50, p95, p99)
- **Infrastructure Metrics**: CPU, memory, disk, network I/O
- **Database Metrics**: Connection pool size, query duration, deadlocks
- **AI Service Metrics**: Gemini API calls, token consumption, cost tracking
- **Business Metrics**: Contracts analyzed, users registered, conversion rate

### Alerting Rules

Critical alerts configured in `monitoring/prometheus/alert_rules.yml`:

- **High Error Rate**: >10% 5xx responses in 5 minutes
- **High Latency**: p95 latency >2s for 5 minutes
- **Service Down**: Health check failure for 2 minutes
- **Database Connection Pool**: >80% pool utilization
- **High Memory Usage**: >85% memory utilization
- **Pod Crash Loop**: Container restart count >3 in 10 minutes

### Log Aggregation

- **Application Logs**: Structured JSON logging with correlation IDs
- **Access Logs**: Nginx/FastAPI request logs
- **Error Tracking**: Sentry integration for exception tracking
- **Audit Logs**: Authentication events, contract analysis requests

---

## Security

### Authentication & Authorization

- **JWT Tokens**: RS256 algorithm with short expiration (30 minutes)
- **Password Hashing**: bcrypt with salt rounds
- **Session Management**: Redis-backed sessions with TTL
- **RBAC**: Role-based access control (admin, user, read-only)
- **API Keys**: Rate-limited API access for programmatic use

### Network Security

- **VPC Isolation**: Private subnets for backend and database
- **Security Groups**: Principle of least privilege
- **Network Policies**: Kubernetes network segmentation
- **SSL/TLS**: End-to-end encryption with AWS ACM certificates
- **WAF**: AWS WAF for DDoS protection and SQL injection prevention

### Application Security

- **Input Validation**: Pydantic models with strict type checking
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **XSS Protection**: Content Security Policy headers
- **CSRF Protection**: SameSite cookies and CSRF tokens
- **Dependency Scanning**: Automated vulnerability scanning in CI/CD
- **Container Security**: Non-root containers, read-only filesystem, capability dropping

### Data Security

- **Encryption at Rest**: AWS RDS encryption, S3 SSE-KMS
- **Encryption in Transit**: TLS 1.3 for all connections
- **Secrets Management**: Kubernetes Secrets, AWS Secrets Manager
- **Backup Encryption**: Encrypted backups with retention policies
- **PII Protection**: Data masking, GDPR compliance considerations

---

## Performance Optimization

### Backend Optimization

- **Connection Pooling**: PostgreSQL connection pooling (10-30 connections)
- **Redis Caching**: API response caching with TTL
- **Async Processing**: FastAPI async endpoints for I/O operations
- **Query Optimization**: Database indexes on frequently queried columns
- **API Pagination**: Limit query results to prevent memory exhaustion

### Frontend Optimization

- **Code Splitting**: React lazy loading for routes
- **Bundle Optimization**: Vite tree-shaking and minification
- **CDN Delivery**: CloudFront for static assets
- **Image Optimization**: WebP format, lazy loading
- **Service Worker**: PWA capabilities for offline access

### Infrastructure Optimization

- **Auto-scaling**: HPA for dynamic resource allocation
- **Load Balancing**: AWS ALB with health-based routing
- **CDN Caching**: CloudFront edge caching for static content
- **Database Read Replicas**: Offload read traffic from primary
- **Resource Right-sizing**: Monitoring-driven instance sizing

---

## Cost Optimization

### AWS Free Tier Utilization

- **EC2**: t2.micro instances for development
- **RDS**: db.t3.micro for testing
- **S3**: 5GB storage included
- **CloudWatch**: Basic monitoring included

### Cost Reduction Strategies

- **Spot Instances**: 70% cost savings for non-critical workloads
- **Reserved Instances**: 40% savings for production databases
- **S3 Lifecycle Policies**: Transition to Glacier for archival
- **Auto-scaling**: Scale down during off-peak hours
- **Resource Tagging**: Cost allocation and chargeback

### Estimated Monthly Costs

- **Development Environment**: $20-30/month (mostly within free tier)
- **Production Environment**: $150-250/month (optimized with spot instances)
- **High-Traffic Production**: $500-1000/month (with auto-scaling and CDN)

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the Repository**: Create your feature branch
2. **Write Tests**: Ensure new features have unit and integration tests
3. **Code Quality**: Run linters (flake8, black, eslint) before committing
4. **Documentation**: Update relevant documentation for new features
5. **Pull Request**: Provide clear description of changes and reasoning

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
docker-compose up -d
pytest tests/ -v

# Commit with conventional commits
git commit -m "feat: add contract comparison feature"

# Push and create PR
git push origin feature/your-feature-name
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## Links

- **Documentation**: [docs/architecture.md](docs/architecture.md)
- **API Documentation**: http://localhost:8000/docs (when running locally)
- **Frontend Demo**: https://smart-contract-rewriter.vercel.app
- **Monitoring Dashboard**: http://localhost:3001 (Grafana)
- **Metrics**: http://localhost:9090 (Prometheus)

---

## Acknowledgments

- **Google Gemini AI**: For advanced smart contract analysis
- **OpenZeppelin**: For secure contract patterns and libraries
- **FastAPI**: For modern async Python web framework
- **React**: For robust frontend development
- **Kubernetes Community**: For orchestration best practices
- **AWS**: For cloud infrastructure services

---

## Contact

For questions, feature requests, or collaboration:

- **GitHub Issues**: [Submit an issue](https://github.com/yourusername/smart-contract-rewriter/issues)
- **Email**: your.email@example.com
- **LinkedIn**: [Your LinkedIn Profile](https://linkedin.com/in/yourprofile)

---

**Built with expertise in DevOps, Cloud Architecture, and Full-Stack Development**

*Demonstrating competencies from Phase 1 through Phase 6 of professional DevOps engineering*
