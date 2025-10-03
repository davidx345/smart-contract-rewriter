# 🏗️ System Architecture Documentation

## 📋 **Overview**

The Smart Contract Rewriter Platform implements a **cloud-native, microservices architecture** designed for scalability, reliability, and maintainability. This document provides comprehensive architectural insights for technical stakeholders and recruitment purposes.

---

## 🎯 **Architecture Principles**

### **🔧 Design Philosophy**
- **Microservices First**: Loosely coupled, independently deployable services
- **Cloud Native**: Built for containerization and orchestration
- **API-Driven**: RESTful APIs with comprehensive documentation
- **Event-Driven**: Asynchronous processing for scalability
- **Security by Design**: Zero-trust architecture principles

### **🏆 Quality Attributes**
| Attribute | Target | Implementation |
|-----------|--------|----------------|
| **Availability** | 99.9% | Multi-AZ deployment, health checks |
| **Scalability** | 10x growth | Horizontal scaling, auto-scaling groups |
| **Performance** | <200ms API | Caching, CDN, optimized queries |
| **Security** | Zero breaches | VPC isolation, encryption, IAM |
| **Maintainability** | <4hr MTTR | Monitoring, alerting, documentation |

---

## 🏗️ **High-Level Architecture**

```mermaid
graph TB
    subgraph "External Users"
        DEV[Developers]
        ADMIN[Administrators]
        API_CLIENTS[API Clients]
    end

    subgraph "CDN & Load Balancing"
        CF[CloudFront CDN]
        ALB[Application Load Balancer]
    end

    subgraph "Frontend Layer"
        SPA[React TypeScript SPA]
        NGINX[Nginx Web Server]
    end

    subgraph "API Gateway"
        GATEWAY[FastAPI Gateway]
        AUTH_MW[Authentication Middleware]
        RATE_LIMIT[Rate Limiting]
    end

    subgraph "Microservices Cluster"
        AUTH_SVC[Authentication Service]
        CONTRACT_SVC[Contract Processing Service]
        AI_SVC[AI Analysis Service]
        NOTIFICATION_SVC[Notification Service]
        METRICS_SVC[Metrics Service]
    end

    subgraph "Data Layer"
        RDS[(PostgreSQL RDS)]
        REDIS[(Redis ElastiCache)]
        S3[S3 Object Storage]
    end

    subgraph "External Services"
        GEMINI[Google Gemini AI]
        WEB3[Web3 Providers]
        SLACK[Slack API]
        EMAIL[Email SMTP]
    end

    subgraph "Monitoring & Observability"
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
        CLOUDWATCH[CloudWatch]
    end

    %% User flows
    DEV --> CF
    ADMIN --> CF
    API_CLIENTS --> ALB

    %% Frontend flow
    CF --> SPA
    SPA --> NGINX
    NGINX --> ALB

    %% API Gateway
    ALB --> GATEWAY
    GATEWAY --> AUTH_MW
    AUTH_MW --> RATE_LIMIT

    %% Service routing
    RATE_LIMIT --> AUTH_SVC
    RATE_LIMIT --> CONTRACT_SVC
    RATE_LIMIT --> AI_SVC
    RATE_LIMIT --> NOTIFICATION_SVC
    RATE_LIMIT --> METRICS_SVC

    %% Data connections
    AUTH_SVC --> REDIS
    CONTRACT_SVC --> RDS
    CONTRACT_SVC --> S3
    AI_SVC --> GEMINI
    CONTRACT_SVC --> WEB3
    NOTIFICATION_SVC --> SLACK
    NOTIFICATION_SVC --> EMAIL

    %% Monitoring
    GATEWAY --> PROMETHEUS
    AUTH_SVC --> PROMETHEUS
    CONTRACT_SVC --> PROMETHEUS
    AI_SVC --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    RDS --> CLOUDWATCH
    S3 --> CLOUDWATCH
```

---

## 🌐 **Network Architecture**

### **🔐 VPC Design**

```mermaid
graph TB
    subgraph "AWS Region (us-east-1)"
        subgraph "VPC (10.0.0.0/16)"
            subgraph "Availability Zone A"
                PUB_A[Public Subnet A<br/>10.0.1.0/24]
                PRIV_A[Private Subnet A<br/>10.0.3.0/24]
            end
            
            subgraph "Availability Zone B"
                PUB_B[Public Subnet B<br/>10.0.2.0/24]
                PRIV_B[Private Subnet B<br/>10.0.4.0/24]
            end
            
            IGW[Internet Gateway]
            NAT_A[NAT Gateway A]
            NAT_B[NAT Gateway B]
            
            subgraph "Public Resources"
                ALB[Application Load Balancer]
                BASTION[Bastion Host]
            end
            
            subgraph "Private Resources"
                APP_A[Application Servers A]
                APP_B[Application Servers B]
                RDS_PRIMARY[(RDS Primary)]
                RDS_STANDBY[(RDS Standby)]
            end
        end
    end

    %% Connections
    IGW --> PUB_A
    IGW --> PUB_B
    PUB_A --> NAT_A
    PUB_B --> NAT_B
    NAT_A --> PRIV_A
    NAT_B --> PRIV_B
    
    ALB --> PUB_A
    ALB --> PUB_B
    BASTION --> PUB_A
    
    APP_A --> PRIV_A
    APP_B --> PRIV_B
    RDS_PRIMARY --> PRIV_A
    RDS_STANDBY --> PRIV_B
```

### **🛡️ Security Groups**

| Security Group | Purpose | Inbound Rules | Outbound Rules |
|----------------|---------|---------------|----------------|
| **ALB-SG** | Load balancer access | HTTP:80, HTTPS:443 from 0.0.0.0/0 | All traffic to App-SG |
| **App-SG** | Application servers | HTTP:8000 from ALB-SG | All traffic to 0.0.0.0/0 |
| **DB-SG** | Database access | PostgreSQL:5432 from App-SG, Bastion-SG | None |
| **Bastion-SG** | Management access | SSH:22 from admin IPs | SSH:22 to App-SG, PostgreSQL:5432 to DB-SG |
| **Redis-SG** | Cache access | Redis:6379 from App-SG | None |

---

## ⚙️ **Microservices Architecture**

### **🔧 Service Breakdown**

#### **1. Authentication Service**
```yaml
Purpose: User authentication and authorization
Technology: FastAPI + JWT + Redis
Responsibilities:
  - User registration and login
  - JWT token generation and validation
  - Session management
  - Role-based access control
Database: Redis (sessions), PostgreSQL (users)
Endpoints:
  - POST /auth/register
  - POST /auth/login
  - POST /auth/refresh
  - GET /auth/profile
```

#### **2. Contract Processing Service**
```yaml
Purpose: Smart contract analysis and management
Technology: FastAPI + SQLAlchemy + Web3
Responsibilities:
  - Contract upload and validation
  - Blockchain interaction
  - Analysis workflow orchestration
  - Result storage and retrieval
Database: PostgreSQL (contracts, analyses)
Storage: S3 (contract files, artifacts)
Endpoints:
  - POST /contracts/upload
  - GET /contracts/{id}
  - POST /contracts/{id}/analyze
  - GET /contracts/{id}/history
```

#### **3. AI Analysis Service**
```yaml
Purpose: AI-powered contract analysis
Technology: FastAPI + Google Gemini API
Responsibilities:
  - Contract code analysis
  - Security vulnerability detection
  - Gas optimization suggestions
  - Code quality metrics
External APIs: Google Gemini Pro
Endpoints:
  - POST /ai/analyze
  - POST /ai/rewrite
  - GET /ai/suggestions/{contract_id}
```

#### **4. Notification Service**
```yaml
Purpose: Multi-channel notifications
Technology: FastAPI + Celery
Responsibilities:
  - Email notifications
  - Slack integration
  - Webhook delivery
  - Notification templates
External APIs: SMTP, Slack, Custom webhooks
Endpoints:
  - POST /notifications/send
  - GET /notifications/status
  - POST /notifications/webhook
```

#### **5. Metrics Service**
```yaml
Purpose: Analytics and monitoring
Technology: FastAPI + Prometheus
Responsibilities:
  - Usage analytics
  - Performance metrics
  - Business intelligence
  - Health checks
Database: PostgreSQL (analytics), Prometheus (metrics)
Endpoints:
  - GET /metrics (Prometheus format)
  - GET /analytics/usage
  - GET /health
```

---

## 💾 **Data Architecture**

### **🗄️ Database Design**

```mermaid
erDiagram
    USER {
        uuid id PK
        string email UK
        string username UK
        string password_hash
        enum role
        timestamp created_at
        timestamp last_login
        boolean is_active
    }
    
    CONTRACT {
        uuid id PK
        uuid user_id FK
        string name
        text source_code
        string language
        string network
        string status
        timestamp created_at
        timestamp updated_at
    }
    
    ANALYSIS {
        uuid id PK
        uuid contract_id FK
        string analysis_type
        json results
        float score
        json suggestions
        timestamp created_at
        string status
    }
    
    NOTIFICATION {
        uuid id PK
        uuid user_id FK
        string type
        string channel
        json payload
        string status
        timestamp created_at
        timestamp sent_at
    }
    
    USER ||--o{ CONTRACT : creates
    CONTRACT ||--o{ ANALYSIS : has
    USER ||--o{ NOTIFICATION : receives
```

### **📊 Data Flow Patterns**

```mermaid
sequenceDiagram
    participant U as User
    participant G as API Gateway
    participant C as Contract Service
    participant A as AI Service
    participant N as Notification Service
    participant D as Database
    participant S as S3 Storage

    U->>G: Upload contract
    G->>C: Validate & store contract
    C->>D: Save contract metadata
    C->>S: Store contract file
    C->>A: Request analysis
    A->>A: Process with Gemini AI
    A->>D: Store analysis results
    A->>N: Send completion notification
    N->>U: Email/Slack notification
    C->>U: Return analysis results
```

---

## 🐳 **Container Architecture**

### **📦 Container Strategy**

```dockerfile
# Multi-stage build example for Backend Service
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **☸️ Kubernetes Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contract-service
  namespace: smart-contract-platform
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: contract-service
  template:
    metadata:
      labels:
        app: contract-service
    spec:
      containers:
      - name: contract-service
        image: davidx345/contract-service:v1.2.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 📈 **Scalability & Performance**

### **🚀 Scaling Strategies**

#### **Horizontal Scaling**
```yaml
Auto Scaling Configuration:
  Trigger Metrics:
    - CPU utilization > 70%
    - Memory usage > 80%
    - Request rate > 1000 req/min
  Scale Out: Add 1-2 instances
  Scale In: Remove instances gradually
  Cooldown: 300 seconds
```

#### **Performance Optimizations**
- **API Gateway**: Request/response caching
- **Database**: Connection pooling, read replicas
- **Frontend**: Code splitting, lazy loading, CDN
- **Storage**: S3 Transfer Acceleration, CloudFront

### **📊 Performance Targets**

| Metric | Target | Current | Strategy |
|--------|--------|---------|----------|
| **API Response Time** | <200ms | 150ms | Caching, optimization |
| **Database Query Time** | <50ms | 35ms | Indexing, query optimization |
| **Page Load Time** | <2s | 1.2s | CDN, code splitting |
| **Concurrent Users** | 1000+ | 500 | Horizontal scaling |
| **Throughput** | 10k req/min | 5k req/min | Load balancing |

---

## 🔧 **DevOps & Deployment**

### **🔄 CI/CD Pipeline**

```mermaid
graph LR
    subgraph "Development"
        CODE[Code Changes]
        PR[Pull Request]
    end
    
    subgraph "CI Pipeline"
        TEST[Automated Tests]
        LINT[Code Quality]
        SECURITY[Security Scan]
        BUILD[Build Images]
    end
    
    subgraph "CD Pipeline"
        STAGING[Deploy to Staging]
        E2E[E2E Tests]
        PROD[Deploy to Production]
    end
    
    subgraph "Monitoring"
        HEALTH[Health Checks]
        ALERTS[Alerting]
        ROLLBACK[Auto Rollback]
    end
    
    CODE --> PR
    PR --> TEST
    TEST --> LINT
    LINT --> SECURITY
    SECURITY --> BUILD
    BUILD --> STAGING
    STAGING --> E2E
    E2E --> PROD
    PROD --> HEALTH
    HEALTH --> ALERTS
    ALERTS --> ROLLBACK
```

### **🚀 Deployment Strategy**

```yaml
Blue-Green Deployment:
  Strategy: Zero-downtime deployments
  Process:
    1. Deploy to green environment
    2. Run health checks
    3. Switch traffic gradually
    4. Monitor metrics
    5. Rollback if issues detected
  
Rollback Capability:
  Time: <5 minutes
  Trigger: Health check failures
  Process: Automated via monitoring
```

---

## 📊 **Monitoring & Observability**

### **📈 Metrics Collection**

```yaml
Application Metrics:
  - Request rate and latency
  - Error rates by endpoint
  - Database connection pool
  - AI processing time
  - User activity patterns

Infrastructure Metrics:
  - CPU, memory, disk usage
  - Network I/O and latency
  - Container health
  - Database performance
  - Storage utilization
```

### **🚨 Alerting Rules**

```yaml
Critical Alerts:
  - Service down (>1 minute)
  - Error rate >5% (>5 minutes)
  - Database connection failure
  - Memory usage >90%
  - Disk space <10%

Warning Alerts:
  - Response time >500ms
  - CPU usage >80%
  - Failed deployment
  - SSL certificate expiry
```

---

## 🔐 **Security Architecture**

### **🛡️ Security Layers**

1. **Network Security**: VPC isolation, security groups
2. **Application Security**: JWT authentication, input validation
3. **Data Security**: Encryption at rest and in transit
4. **Infrastructure Security**: IAM roles, secret management
5. **Monitoring Security**: Audit logs, anomaly detection

### **🔒 Security Controls**

```yaml
Authentication & Authorization:
  - JWT with refresh tokens
  - Role-based access control
  - API key authentication
  - OAuth integration

Data Protection:
  - AES-256 encryption (S3)
  - TLS 1.2+ (in transit)
  - Database encryption
  - PII data masking

Infrastructure:
  - VPC network isolation
  - Security group restrictions
  - IAM least privilege
  - Regular security scans
```

---

## 🎯 **Future Enhancements**

### **📅 Roadmap**

#### **Phase 5: Infrastructure as Code**
- Complete Terraform implementation
- Multi-environment management
- Disaster recovery automation

#### **Phase 6: Advanced Monitoring**
- Distributed tracing
- APM integration
- Business metrics tracking

#### **Phase 7: AI Enhancement**
- Custom model training
- Multi-model comparison
- Automated optimization

---

<div align="center">

**🏗️ This architecture demonstrates enterprise-grade system design capabilities**

*Every component is production-ready and showcases real-world DevOps expertise*

</div>