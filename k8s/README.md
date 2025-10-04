# Smart Contract Rewriter - Kubernetes Documentation
# Phase 6: Container Orchestration & Auto-scaling

## Overview
This directory contains production-ready Kubernetes manifests for deploying the Smart Contract Rewriter application with enterprise-grade features including auto-scaling, monitoring, security, and high availability.

## Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│     Ingress     │────│    Frontend     │
│      (ALB)      │    │   (AWS ALB)     │    │   (React/Nginx) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Backend     │
                       │   (FastAPI)     │
                       └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │ PostgreSQL  │ │    Redis    │ │ Prometheus  │
        │ (Database)  │ │   (Cache)   │ │(Monitoring) │
        └─────────────┘ └─────────────┘ └─────────────┘
```

## File Structure
```
k8s/
├── 00-namespace.yaml           # Namespace with resource quotas
├── 01-configmaps.yaml         # Application configuration
├── 02-secrets.yaml            # Sensitive data (passwords, API keys)
├── 03-storage.yaml            # Persistent storage claims
├── 04-postgres.yaml           # PostgreSQL database
├── 05-redis.yaml              # Redis cache
├── 06-backend.yaml            # FastAPI backend with HPA
├── 07-frontend.yaml           # React frontend with Nginx
├── 08-ingress-networking.yaml # Ingress & Network policies
├── 09-rbac.yaml               # Role-based access control
├── 10-database-init.yaml      # Database initialization
├── 11-monitoring.yaml         # Prometheus monitoring
├── deploy.sh                  # Deployment automation script
└── README.md                  # This file
```

## Key Features

### 🔄 Auto-scaling
- **Backend HPA**: 2-10 replicas based on CPU (70%) and Memory (80%)
- **Frontend HPA**: 2-5 replicas based on CPU usage
- **Graceful scaling** with stabilization windows

### 🛡️ Security
- **Network Policies**: Micro-segmentation between services
- **RBAC**: Least-privilege access control
- **Security Context**: Non-root containers, read-only filesystem
- **Resource Limits**: CPU/Memory limits and requests
- **Secret Management**: Base64 encoded secrets for sensitive data

### 📊 Monitoring & Observability
- **Prometheus**: Metrics collection and alerting
- **Health Checks**: Liveness, readiness, and startup probes
- **Logging**: Structured logs with proper labels
- **Metrics**: Custom application metrics endpoint

### 🚀 High Availability
- **Multi-replica deployments** for stateless services
- **Rolling updates** with zero downtime
- **Persistent storage** for stateful services
- **Load balancing** across multiple pods

### 🌐 Networking
- **AWS Application Load Balancer** with SSL termination
- **Ingress routing** for frontend and API
- **Service mesh ready** architecture
- **DNS-based service discovery**

## Quick Start

### Prerequisites
```bash
# Install kubectl
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Configure kubectl for your cluster
aws eks update-kubeconfig --region us-west-2 --name smart-contract-cluster
```

### Deployment
```bash
# Navigate to k8s directory
cd k8s/

# Make deployment script executable
chmod +x deploy.sh

# Full deployment
./deploy.sh deploy

# Or step by step:
./deploy.sh build     # Build Docker images
./deploy.sh deploy    # Deploy to Kubernetes
./deploy.sh status    # Check deployment status
./deploy.sh health    # Run health checks
```

### Cleanup
```bash
./deploy.sh cleanup
```

## Configuration

### Environment Variables
Update `01-configmaps.yaml` for application configuration:
- Database settings
- API configuration
- CORS origins
- Rate limiting
- Feature flags

### Secrets
Update `02-secrets.yaml` with base64 encoded values:
```bash
# Encode secrets
echo -n "your-password" | base64

# Decode secrets (for verification)
echo "cGFzc3dvcmQ=" | base64 -d
```

### Resource Allocation
Adjust resource requests/limits in deployment files:
- Backend: 200m CPU, 256Mi RAM (requests) → 500m CPU, 512Mi RAM (limits)
- Frontend: 50m CPU, 64Mi RAM (requests) → 100m CPU, 128Mi RAM (limits)
- Database: 250m CPU, 512Mi RAM (requests) → 500m CPU, 1Gi RAM (limits)

## Monitoring

### Prometheus Metrics
Access Prometheus dashboard:
```bash
kubectl port-forward service/prometheus 9090:9090 --namespace=smart-contract-rewriter
# Visit http://localhost:9090
```

### Key Metrics to Monitor
- `http_requests_total` - Request count and status codes
- `http_request_duration_seconds` - Request latency
- `container_memory_usage_bytes` - Memory consumption
- `container_cpu_usage_seconds_total` - CPU usage
- `postgres_up` - Database availability
- `redis_up` - Cache availability

### Alerts
Configured alerts for:
- High error rate (>10% 5xx responses)
- High memory usage (>80%)
- High CPU usage (>80%)
- Database/Redis downtime
- Service unavailability

## Scaling

### Manual Scaling
```bash
# Scale backend
kubectl scale deployment backend --replicas=5 --namespace=smart-contract-rewriter

# Scale frontend
kubectl scale deployment frontend --replicas=3 --namespace=smart-contract-rewriter
```

### Auto-scaling Configuration
HPA configuration in deployment files:
- **Scale up**: When CPU/Memory > thresholds for 60 seconds
- **Scale down**: When CPU/Memory < thresholds for 300 seconds
- **Rate limiting**: Prevent thrashing with stabilization windows

## Networking & Security

### Network Policies
- **Default deny all**: Block all traffic by default
- **Allow frontend → backend**: HTTP traffic on port 8000
- **Allow backend → database**: PostgreSQL traffic on port 5432
- **Allow backend → redis**: Redis traffic on port 6379
- **Allow external → frontend**: HTTP/HTTPS traffic
- **Allow DNS**: UDP/TCP traffic on port 53
- **Allow HTTPS egress**: External API calls

### Ingress Configuration
- **AWS ALB**: Internet-facing Application Load Balancer
- **SSL termination**: HTTPS with ACM certificates
- **Path-based routing**: `/api/*` → backend, `/` → frontend
- **Health checks**: Custom health check endpoints
- **WAF integration**: AWS WAF for DDoS and security

## Troubleshooting

### Common Issues

#### Pods Not Starting
```bash
# Check pod status
kubectl get pods --namespace=smart-contract-rewriter

# Check pod logs
kubectl logs -f deployment/backend --namespace=smart-contract-rewriter

# Describe pod for events
kubectl describe pod <pod-name> --namespace=smart-contract-rewriter
```

#### Database Connection Issues
```bash
# Check database pod
kubectl logs -f deployment/postgres --namespace=smart-contract-rewriter

# Test database connectivity
kubectl exec -it deployment/backend --namespace=smart-contract-rewriter -- psql $DATABASE_URL
```

#### Image Pull Errors
```bash
# Check if images exist
docker images | grep smart-contract-rewriter

# Rebuild images
./deploy.sh build
```

#### Resource Constraints
```bash
# Check resource usage
kubectl top pods --namespace=smart-contract-rewriter
kubectl top nodes

# Check resource quotas
kubectl describe resourcequota --namespace=smart-contract-rewriter
```

### Debug Commands
```bash
# Get all resources
kubectl get all --namespace=smart-contract-rewriter

# Check events
kubectl get events --namespace=smart-contract-rewriter --sort-by='.lastTimestamp'

# Port forward for local testing
kubectl port-forward service/backend-service 8000:8000 --namespace=smart-contract-rewriter
kubectl port-forward service/frontend-service 3000:80 --namespace=smart-contract-rewriter

# Execute into pods
kubectl exec -it deployment/backend --namespace=smart-contract-rewriter -- bash
kubectl exec -it deployment/postgres --namespace=smart-contract-rewriter -- psql -U postgres
```

## Performance Tuning

### Database Optimization
- **Connection pooling**: Configure in backend application
- **Index optimization**: Monitor slow queries
- **Resource allocation**: Adjust CPU/memory based on load

### Application Optimization
- **JVM tuning**: For Java applications
- **Python workers**: Adjust Gunicorn workers for FastAPI
- **Caching strategy**: Implement Redis caching patterns

### Cluster Optimization
- **Node sizing**: Right-size EC2 instances
- **Pod distribution**: Use anti-affinity rules
- **Storage performance**: Use gp3 volumes for better IOPS

## Security Best Practices

### Container Security
- Use minimal base images (Alpine)
- Run as non-root user
- Read-only root filesystem
- Drop all capabilities
- Security scanning with tools like Trivy

### Network Security
- Implement network policies
- Use service mesh for mTLS
- Regular security audits
- Monitor traffic patterns

### Data Security
- Encrypt data at rest
- Encrypt data in transit
- Regular backup strategies
- Implement audit logging

## Backup & Disaster Recovery

### Database Backups
```bash
# Manual backup
kubectl exec deployment/postgres --namespace=smart-contract-rewriter -- pg_dump -U postgres smart_contracts > backup.sql

# Automated backups with CronJob (add to manifests)
```

### Configuration Backups
```bash
# Export all manifests
kubectl get all --namespace=smart-contract-rewriter -o yaml > backup-manifests.yaml
```

## Next Steps: Phase 7 - GitOps & CI/CD
- ArgoCD implementation
- GitOps workflows
- Automated testing pipelines
- Progressive delivery strategies
- Multi-environment management

---

**🎯 Phase 6 Complete!** You now have a production-ready Kubernetes deployment with auto-scaling, monitoring, and enterprise security features. Ready for Phase 7?