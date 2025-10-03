# 🎨 Visual Architecture Gallery

This document contains comprehensive visual representations of the Smart Contract Rewriter Platform architecture, designed for technical stakeholders and recruitment purposes.

---

## 📋 **Diagram Index**

- [🏗️ System Architecture Overview](#️-system-architecture-overview)
- [🌐 Network Topology](#-network-topology)
- [📊 Data Flow Diagrams](#-data-flow-diagrams)
- [🚀 Deployment Pipeline](#-deployment-pipeline)
- [🔐 Security Architecture](#-security-architecture)
- [📈 Monitoring Architecture](#-monitoring-architecture)

---

## 🏗️ **System Architecture Overview**

### **High-Level Component Architecture**

```mermaid
graph TB
    subgraph "User Layer"
        WEB[Web Browser]
        MOBILE[Mobile App]
        API_CLIENT[API Clients]
    end

    subgraph "CDN & Edge"
        CF[CloudFront CDN]
        WAF[Web Application Firewall]
    end

    subgraph "Load Balancing"
        ALB[Application Load Balancer]
        NLB[Network Load Balancer]
    end

    subgraph "Application Services"
        subgraph "Frontend Tier"
            REACT[React App]
            NGINX[Nginx Server]
        end
        
        subgraph "API Gateway"
            GATEWAY[FastAPI Gateway]
            AUTH_MW[Auth Middleware]
            RATE_LIMIT[Rate Limiter]
        end
        
        subgraph "Microservices"
            AUTH[Auth Service]
            CONTRACT[Contract Service]
            AI[AI Service]
            NOTIFY[Notification Service]
            METRICS[Metrics Service]
        end
    end

    subgraph "Data & Storage"
        subgraph "Databases"
            RDS[(PostgreSQL RDS)]
            REDIS[(Redis Cache)]
        end
        
        subgraph "Object Storage"
            S3[S3 Bucket]
            S3_ARCHIVE[S3 Glacier]
        end
    end

    subgraph "External Services"
        GEMINI[Google Gemini AI]
        WEB3[Web3 Providers]
        SLACK_API[Slack API]
        SMTP[Email SMTP]
    end

    subgraph "Monitoring & Logging"
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
        CLOUDWATCH[CloudWatch]
        ELK[ELK Stack]
    end

    %% User connections
    WEB --> CF
    MOBILE --> CF
    API_CLIENT --> ALB

    %% CDN and Security
    CF --> WAF
    WAF --> ALB
    ALB --> NGINX
    ALB --> GATEWAY

    %% Frontend
    NGINX --> REACT

    %% API Gateway
    GATEWAY --> AUTH_MW
    AUTH_MW --> RATE_LIMIT
    RATE_LIMIT --> AUTH
    RATE_LIMIT --> CONTRACT
    RATE_LIMIT --> AI
    RATE_LIMIT --> NOTIFY
    RATE_LIMIT --> METRICS

    %% Data connections
    AUTH --> REDIS
    CONTRACT --> RDS
    CONTRACT --> S3
    AI --> GEMINI
    CONTRACT --> WEB3
    NOTIFY --> SLACK_API
    NOTIFY --> SMTP

    %% Storage lifecycle
    S3 --> S3_ARCHIVE

    %% Monitoring
    GATEWAY --> PROMETHEUS
    AUTH --> PROMETHEUS
    CONTRACT --> PROMETHEUS
    AI --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    RDS --> CLOUDWATCH
    S3 --> CLOUDWATCH

    %% Styling
    classDef userLayer fill:#e1f5fe
    classDef frontend fill:#f3e5f5
    classDef api fill:#e8f5e8
    classDef services fill:#fff3e0
    classDef data fill:#fce4ec
    classDef external fill:#f1f8e9
    classDef monitoring fill:#fff8e1

    class WEB,MOBILE,API_CLIENT userLayer
    class REACT,NGINX frontend
    class GATEWAY,AUTH_MW,RATE_LIMIT api
    class AUTH,CONTRACT,AI,NOTIFY,METRICS services
    class RDS,REDIS,S3,S3_ARCHIVE data
    class GEMINI,WEB3,SLACK_API,SMTP external
    class PROMETHEUS,GRAFANA,CLOUDWATCH,ELK monitoring
```

### **Service Layer Detail**

```mermaid
graph LR
    subgraph "Frontend Layer"
        UI[React TypeScript SPA]
        UI_COMP[UI Components]
        UI_STATE[State Management]
    end

    subgraph "API Gateway Layer"
        GW[FastAPI Gateway]
        AUTH_M[Authentication]
        VALID[Validation]
        ROUTE[Routing]
    end

    subgraph "Business Logic Layer"
        AUTH_SVC[Authentication Service]
        CONTRACT_SVC[Contract Service]
        AI_SVC[AI Analysis Service]
        NOTIFY_SVC[Notification Service]
    end

    subgraph "Data Access Layer"
        ORM[SQLAlchemy ORM]
        CACHE[Redis Client]
        S3_CLIENT[S3 Client]
    end

    subgraph "Infrastructure Layer"
        DB[(PostgreSQL)]
        REDIS_DB[(Redis)]
        S3_STORE[S3 Storage]
    end

    UI --> UI_COMP
    UI_COMP --> UI_STATE
    UI_STATE --> GW

    GW --> AUTH_M
    AUTH_M --> VALID
    VALID --> ROUTE

    ROUTE --> AUTH_SVC
    ROUTE --> CONTRACT_SVC
    ROUTE --> AI_SVC
    ROUTE --> NOTIFY_SVC

    AUTH_SVC --> ORM
    CONTRACT_SVC --> ORM
    CONTRACT_SVC --> S3_CLIENT
    AI_SVC --> CACHE
    NOTIFY_SVC --> CACHE

    ORM --> DB
    CACHE --> REDIS_DB
    S3_CLIENT --> S3_STORE
```

---

## 🌐 **Network Topology**

### **AWS VPC Architecture**

```mermaid
graph TB
    subgraph "Internet"
        USERS[Users]
        ADMINS[Administrators]
    end

    subgraph "AWS Cloud (us-east-1)"
        subgraph "VPC (10.0.0.0/16)"
            subgraph "Availability Zone A (us-east-1a)"
                subgraph "Public Subnet A (10.0.1.0/24)"
                    ALB_A[Load Balancer A]
                    NAT_A[NAT Gateway A]
                    BASTION[Bastion Host]
                end
                
                subgraph "Private Subnet A (10.0.3.0/24)"
                    APP_A[App Server A]
                    RDS_PRIMARY[(RDS Primary)]
                end
            end

            subgraph "Availability Zone B (us-east-1b)"
                subgraph "Public Subnet B (10.0.2.0/24)"
                    ALB_B[Load Balancer B]
                    NAT_B[NAT Gateway B]
                end
                
                subgraph "Private Subnet B (10.0.4.0/24)"
                    APP_B[App Server B]
                    RDS_STANDBY[(RDS Standby)]
                    REDIS[(ElastiCache)]
                end
            end

            IGW[Internet Gateway]
            RT_PUB[Public Route Table]
            RT_PRIV_A[Private Route Table A]
            RT_PRIV_B[Private Route Table B]
        end

        subgraph "S3 Storage"
            S3[S3 Bucket]
            S3_LOGS[S3 Logs Bucket]
        end
    end

    subgraph "External Services"
        GEMINI[Google Gemini]
        SLACK[Slack API]
    end

    %% User connections
    USERS --> IGW
    ADMINS --> IGW

    %% Internet Gateway
    IGW --> ALB_A
    IGW --> ALB_B
    IGW --> BASTION

    %% Load balancer to apps
    ALB_A --> APP_A
    ALB_B --> APP_B

    %% NAT Gateway connections
    NAT_A --> APP_A
    NAT_B --> APP_B

    %% Database replication
    RDS_PRIMARY -.-> RDS_STANDBY

    %% External API calls
    APP_A --> GEMINI
    APP_B --> GEMINI
    APP_A --> SLACK
    APP_B --> SLACK

    %% Storage
    APP_A --> S3
    APP_B --> S3
    APP_A --> REDIS
    APP_B --> REDIS

    %% Admin access
    BASTION --> APP_A
    BASTION --> APP_B
    BASTION --> RDS_PRIMARY

    %% Styling
    classDef public fill:#ffcdd2
    classDef private fill:#c8e6c9
    classDef database fill:#e1bee7
    classDef storage fill:#ffe0b2
    classDef external fill:#f8bbd9

    class ALB_A,ALB_B,NAT_A,NAT_B,BASTION,IGW public
    class APP_A,APP_B private
    class RDS_PRIMARY,RDS_STANDBY,REDIS database
    class S3,S3_LOGS storage
    class GEMINI,SLACK external
```

### **Security Groups & Network ACLs**

```mermaid
graph TB
    subgraph "Security Group Rules"
        subgraph "ALB Security Group"
            ALB_SG["ALB-SG<br/>Inbound: 80,443 from 0.0.0.0/0<br/>Outbound: 8000 to App-SG"]
        end
        
        subgraph "Application Security Group"
            APP_SG["App-SG<br/>Inbound: 8000 from ALB-SG<br/>Inbound: 22 from Bastion-SG<br/>Outbound: 443 to 0.0.0.0/0<br/>Outbound: 5432 to DB-SG"]
        end
        
        subgraph "Database Security Group"
            DB_SG["DB-SG<br/>Inbound: 5432 from App-SG<br/>Inbound: 5432 from Bastion-SG<br/>Outbound: None"]
        end
        
        subgraph "Bastion Security Group"
            BASTION_SG["Bastion-SG<br/>Inbound: 22 from Admin-IPs<br/>Outbound: 22 to App-SG<br/>Outbound: 5432 to DB-SG"]
        end
    end

    ALB_SG --> APP_SG
    APP_SG --> DB_SG
    BASTION_SG --> APP_SG
    BASTION_SG --> DB_SG
```

---

## 📊 **Data Flow Diagrams**

### **Contract Analysis Workflow**

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant G as API Gateway
    participant A as Auth Service
    participant C as Contract Service
    participant AI as AI Service
    participant DB as Database
    participant S3 as S3 Storage
    participant N as Notification

    U->>F: Upload Contract
    F->>G: POST /contracts/upload
    G->>A: Validate JWT Token
    A-->>G: Token Valid
    G->>C: Process Upload
    C->>DB: Save Contract Metadata
    C->>S3: Store Contract File
    C-->>F: Upload Successful
    
    U->>F: Request Analysis
    F->>G: POST /contracts/{id}/analyze
    G->>A: Validate Permissions
    A-->>G: Authorized
    G->>C: Start Analysis
    C->>S3: Retrieve Contract
    C->>AI: Analyze Contract
    AI->>AI: Process with Gemini
    AI-->>C: Analysis Results
    C->>DB: Store Results
    C->>N: Send Notification
    N->>U: Email/Slack Alert
    C-->>F: Analysis Complete
    F-->>U: Display Results
```

### **User Authentication Flow**

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant G as API Gateway
    participant A as Auth Service
    participant R as Redis Cache
    participant DB as Database
    participant O as OAuth Provider

    alt Traditional Login
        U->>F: Enter Credentials
        F->>G: POST /auth/login
        G->>A: Validate Credentials
        A->>DB: Check User
        DB-->>A: User Data
        A->>A: Verify Password
        A->>R: Store Session
        A-->>F: JWT Tokens
        F-->>U: Login Success
    else OAuth Login
        U->>F: Click OAuth Login
        F->>O: OAuth Request
        O-->>F: Authorization Code
        F->>G: POST /auth/oauth
        G->>A: Exchange Code
        A->>O: Get User Info
        O-->>A: User Profile
        A->>DB: Create/Update User
        A->>R: Store Session
        A-->>F: JWT Tokens
        F-->>U: Login Success
    end
```

### **Data Processing Pipeline**

```mermaid
graph LR
    subgraph "Input Stage"
        UPLOAD[Contract Upload]
        VALIDATE[Validation]
        STORE[Initial Storage]
    end

    subgraph "Processing Stage"
        QUEUE[Job Queue]
        ANALYZE[AI Analysis]
        PROCESS[Code Processing]
    end

    subgraph "Output Stage"
        RESULTS[Store Results]
        NOTIFY[Notifications]
        CACHE[Cache Results]
    end

    subgraph "Storage Layer"
        S3[(S3 Files)]
        DB[(PostgreSQL)]
        REDIS[(Redis Cache)]
    end

    UPLOAD --> VALIDATE
    VALIDATE --> STORE
    STORE --> S3
    STORE --> QUEUE

    QUEUE --> ANALYZE
    ANALYZE --> PROCESS
    PROCESS --> RESULTS

    RESULTS --> DB
    RESULTS --> NOTIFY
    RESULTS --> CACHE
    CACHE --> REDIS

    %% Styling
    classDef input fill:#e3f2fd
    classDef process fill:#f3e5f5
    classDef output fill:#e8f5e8
    classDef storage fill:#fff3e0

    class UPLOAD,VALIDATE,STORE input
    class QUEUE,ANALYZE,PROCESS process
    class RESULTS,NOTIFY,CACHE output
    class S3,DB,REDIS storage
```

---

## 🚀 **Deployment Pipeline**

### **CI/CD Workflow**

```mermaid
graph TB
    subgraph "Development"
        DEV[Developer]
        BRANCH[Feature Branch]
        PR[Pull Request]
    end

    subgraph "CI Pipeline (GitHub Actions)"
        TRIGGER[Trigger Build]
        LINT[Code Linting]
        TEST[Unit Tests]
        SECURITY[Security Scan]
        BUILD[Build Images]
        PUSH[Push to Registry]
    end

    subgraph "CD Pipeline"
        DEPLOY_STAGING[Deploy to Staging]
        E2E[E2E Tests]
        DEPLOY_PROD[Deploy to Production]
        HEALTH[Health Checks]
        ROLLBACK[Auto Rollback]
    end

    subgraph "Infrastructure"
        STAGING[Staging Environment]
        PRODUCTION[Production Environment]
        MONITORING[Monitoring & Alerts]
    end

    DEV --> BRANCH
    BRANCH --> PR
    PR --> TRIGGER

    TRIGGER --> LINT
    LINT --> TEST
    TEST --> SECURITY
    SECURITY --> BUILD
    BUILD --> PUSH

    PUSH --> DEPLOY_STAGING
    DEPLOY_STAGING --> STAGING
    STAGING --> E2E
    E2E --> DEPLOY_PROD
    DEPLOY_PROD --> PRODUCTION
    PRODUCTION --> HEALTH
    HEALTH --> MONITORING
    HEALTH -.-> ROLLBACK

    %% Error flows
    LINT -.-> DEV
    TEST -.-> DEV
    SECURITY -.-> DEV
    E2E -.-> ROLLBACK
    MONITORING -.-> ROLLBACK
```

### **Container Deployment Strategy**

```mermaid
graph TB
    subgraph "Source Control"
        GIT[Git Repository]
        DOCKERFILE[Dockerfiles]
    end

    subgraph "Build Process"
        BUILD[Docker Build]
        SCAN[Security Scan]
        TAG[Image Tagging]
    end

    subgraph "Registry"
        ECR[AWS ECR]
        IMAGES[Container Images]
    end

    subgraph "Orchestration"
        K8S[Kubernetes Cluster]
        DEPLOY[Deployment]
        SERVICE[Services]
        INGRESS[Ingress]
    end

    subgraph "Runtime"
        PODS[Application Pods]
        LB[Load Balancer]
        STORAGE[Persistent Storage]
    end

    GIT --> BUILD
    DOCKERFILE --> BUILD
    BUILD --> SCAN
    SCAN --> TAG
    TAG --> ECR
    ECR --> IMAGES

    IMAGES --> K8S
    K8S --> DEPLOY
    DEPLOY --> PODS
    DEPLOY --> SERVICE
    SERVICE --> LB
    SERVICE --> INGRESS

    PODS --> STORAGE

    %% Styling
    classDef source fill:#e8f5e8
    classDef build fill:#e3f2fd
    classDef registry fill:#f3e5f5
    classDef k8s fill:#fff3e0
    classDef runtime fill:#fce4ec

    class GIT,DOCKERFILE source
    class BUILD,SCAN,TAG build
    class ECR,IMAGES registry
    class K8S,DEPLOY,SERVICE,INGRESS k8s
    class PODS,LB,STORAGE runtime
```

---

## 🔐 **Security Architecture**

### **Zero Trust Security Model**

```mermaid
graph TB
    subgraph "Perimeter Security"
        WAF[Web Application Firewall]
        DDOS[DDoS Protection]
        CDN[CloudFront CDN]
    end

    subgraph "Network Security"
        VPC[VPC Isolation]
        SG[Security Groups]
        NACL[Network ACLs]
        VPN[VPN Gateway]
    end

    subgraph "Application Security"
        AUTH[JWT Authentication]
        RBAC[Role-Based Access]
        RATE[Rate Limiting]
        INPUT[Input Validation]
    end

    subgraph "Data Security"
        ENCRYPT[Encryption at Rest]
        TLS[TLS in Transit]
        SECRETS[Secrets Manager]
        BACKUP[Encrypted Backups]
    end

    subgraph "Monitoring Security"
        AUDIT[Audit Logs]
        SIEM[Security Monitoring]
        ALERTS[Security Alerts]
        INCIDENT[Incident Response]
    end

    WAF --> VPC
    DDOS --> VPC
    CDN --> VPC

    VPC --> AUTH
    SG --> AUTH
    NACL --> AUTH

    AUTH --> ENCRYPT
    RBAC --> ENCRYPT
    INPUT --> TLS

    ENCRYPT --> AUDIT
    SECRETS --> AUDIT
    BACKUP --> SIEM

    %% Styling
    classDef perimeter fill:#ffcdd2
    classDef network fill:#f8bbd9
    classDef app fill:#e1bee7
    classDef data fill:#c8e6c9
    classDef monitor fill:#ffe0b2

    class WAF,DDOS,CDN perimeter
    class VPC,SG,NACL,VPN network
    class AUTH,RBAC,RATE,INPUT app
    class ENCRYPT,TLS,SECRETS,BACKUP data
    class AUDIT,SIEM,ALERTS,INCIDENT monitor
```

---

## 📈 **Monitoring Architecture**

### **Observability Stack**

```mermaid
graph TB
    subgraph "Application Layer"
        APP[Application Services]
        METRICS[Custom Metrics]
        LOGS[Application Logs]
        TRACES[Distributed Traces]
    end

    subgraph "Collection Layer"
        PROM[Prometheus]
        FLUENTD[Fluentd]
        JAEGER[Jaeger]
    end

    subgraph "Storage Layer"
        TSDB[(Time Series DB)]
        ELASTIC[(Elasticsearch)]
        TRACE_DB[(Trace Storage)]
    end

    subgraph "Visualization Layer"
        GRAFANA[Grafana Dashboards]
        KIBANA[Kibana Logs]
        JAEGER_UI[Jaeger UI]
    end

    subgraph "Alerting Layer"
        ALERT_MGR[Alertmanager]
        SLACK[Slack Notifications]
        EMAIL[Email Alerts]
        PAGER[PagerDuty]
    end

    APP --> METRICS
    APP --> LOGS
    APP --> TRACES

    METRICS --> PROM
    LOGS --> FLUENTD
    TRACES --> JAEGER

    PROM --> TSDB
    FLUENTD --> ELASTIC
    JAEGER --> TRACE_DB

    TSDB --> GRAFANA
    ELASTIC --> KIBANA
    TRACE_DB --> JAEGER_UI

    PROM --> ALERT_MGR
    ALERT_MGR --> SLACK
    ALERT_MGR --> EMAIL
    ALERT_MGR --> PAGER

    %% Styling
    classDef app fill:#e3f2fd
    classDef collect fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef visual fill:#fff3e0
    classDef alert fill:#ffcdd2

    class APP,METRICS,LOGS,TRACES app
    class PROM,FLUENTD,JAEGER collect
    class TSDB,ELASTIC,TRACE_DB storage
    class GRAFANA,KIBANA,JAEGER_UI visual
    class ALERT_MGR,SLACK,EMAIL,PAGER alert
```

---

## 📱 **Mobile-First Responsive Design**

All diagrams are optimized for viewing on:
- 🖥️ **Desktop** - Full detail and interactivity
- 📱 **Mobile** - Simplified layouts with touch-friendly navigation
- 📊 **Print** - High-contrast, black & white compatible

---

<div align="center">

**🎨 Visual Architecture Gallery Complete**

*These diagrams demonstrate enterprise-level system design thinking and architectural expertise*

[🔝 Back to Top](#-visual-architecture-gallery) • [📖 Main Documentation](../README.md) • [🏗️ Architecture Guide](architecture.md)

</div>