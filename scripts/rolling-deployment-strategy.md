# 🎯 Rolling Deployment Strategy

## Overview
This document outlines the rolling deployment strategy for the Smart Contract Rewriter microservices platform, ensuring zero-downtime deployments with automatic rollback capabilities.

## 🏗️ **Deployment Architecture**

### **Blue-Green Deployment Pattern**
```yaml
Current State:
  🟦 Blue Environment: Live Production (ports 8000, 8001)
  🟩 Green Environment: Staging/New Version (ports 8002, 8003)

Deployment Flow:
  1. Deploy to Green environment
  2. Health check Green environment
  3. Switch traffic to Green
  4. Retire Blue environment
```

### **Service Topology**
```bash
Load Balancer (nginx)
├── 🟦 unified-main:8000 → 🟩 unified-main:8002
├── 🟦 contract-service:8001 → 🟩 contract-service:8003
└── 🔄 Database (shared between environments)
```

---

## 🚀 **Rolling Deployment Process**

### **Phase 1: Pre-deployment Validation**
```bash
# 1. Environment Health Check
curl -f http://3.87.248.104:8000/health
curl -f http://3.87.248.104:8001/health

# 2. Database Backup
docker exec postgres-container pg_dump smart_contract_db > backup-$(date +%Y%m%d_%H%M%S).sql

# 3. Resource Availability Check
docker system df
free -h
df -h
```

### **Phase 2: Green Environment Deployment**
```bash
# 1. Create green environment containers
docker-compose -f docker-compose.green.yml up -d

# 2. Wait for green environment readiness
./scripts/wait-for-green.sh

# 3. Run integration tests on green
./scripts/test-green-environment.sh
```

### **Phase 3: Traffic Switching**
```bash
# 1. Update nginx configuration
nginx -s reload

# 2. Gradual traffic shift (10% → 50% → 100%)
./scripts/gradual-traffic-shift.sh

# 3. Monitor metrics during transition
./scripts/monitor-deployment.sh
```

### **Phase 4: Blue Environment Retirement**
```bash
# 1. Verify green environment stability
./scripts/verify-deployment.sh

# 2. Stop blue environment
docker-compose -f docker-compose.blue.yml down

# 3. Cleanup old images
docker image prune -f
```

---

## 🛠️ **Implementation Files**

### **1. Green Environment Configuration**
```yaml
# docker-compose.green.yml
version: '3.8'

services:
  unified-main-green:
    build:
      context: .
      dockerfile: Dockerfile.unified
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  contract-service-green:
    build:
      context: .
      dockerfile: Dockerfile.contracts
    ports:
      - "8003:8002"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### **2. Nginx Load Balancer Configuration**
```nginx
# /etc/nginx/conf.d/smart-contract-lb.conf
upstream unified_main {
    server localhost:8000 weight=100;  # Blue
    server localhost:8002 weight=0;    # Green (initially 0)
}

upstream contract_service {
    server localhost:8001 weight=100;  # Blue
    server localhost:8003 weight=0;    # Green (initially 0)
}

server {
    listen 80;
    server_name 3.87.248.104;

    location /api/ {
        proxy_pass http://unified_main;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check endpoint
        location /api/health {
            access_log off;
            proxy_pass http://unified_main;
        }
    }

    location /contracts/ {
        proxy_pass http://contract_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **3. Health Check Script**
```bash
#!/bin/bash
# scripts/wait-for-green.sh

echo "🟩 Waiting for green environment to be ready..."

GREEN_UNIFIED="http://localhost:8002/health"
GREEN_CONTRACT="http://localhost:8003/health"

MAX_ATTEMPTS=30
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    # Check unified-main green
    if curl -f -s $GREEN_UNIFIED > /dev/null; then
        echo "✅ Unified main green is healthy"
        UNIFIED_OK=true
    else
        echo "❌ Unified main green not ready"
        UNIFIED_OK=false
    fi
    
    # Check contract service green
    if curl -f -s $GREEN_CONTRACT > /dev/null; then
        echo "✅ Contract service green is healthy"
        CONTRACT_OK=true
    else
        echo "❌ Contract service green not ready"
        CONTRACT_OK=false
    fi
    
    # Both services ready?
    if [ "$UNIFIED_OK" = true ] && [ "$CONTRACT_OK" = true ]; then
        echo "🎉 Green environment is fully ready!"
        exit 0
    fi
    
    sleep 10
    ATTEMPT=$((ATTEMPT + 1))
done

echo "❌ Green environment failed to become ready within timeout"
exit 1
```

### **4. Gradual Traffic Shift Script**
```bash
#!/bin/bash
# scripts/gradual-traffic-shift.sh

echo "🔄 Starting gradual traffic shift to green environment..."

# Stage 1: 10% traffic to green
echo "Stage 1: 10% traffic to green"
sed -i 's/server localhost:8000 weight=100;/server localhost:8000 weight=90;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8002 weight=0;/server localhost:8002 weight=10;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8001 weight=100;/server localhost:8001 weight=90;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8003 weight=0;/server localhost:8003 weight=10;/' /etc/nginx/conf.d/smart-contract-lb.conf
nginx -s reload
sleep 120  # Monitor for 2 minutes

# Check metrics
if ./scripts/check-error-rate.sh; then
    echo "✅ Stage 1 successful, proceeding to stage 2"
else
    echo "❌ Stage 1 failed, rolling back"
    ./scripts/rollback-traffic.sh
    exit 1
fi

# Stage 2: 50% traffic to green
echo "Stage 2: 50% traffic to green"
sed -i 's/server localhost:8000 weight=90;/server localhost:8000 weight=50;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8002 weight=10;/server localhost:8002 weight=50;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8001 weight=90;/server localhost:8001 weight=50;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8003 weight=10;/server localhost:8003 weight=50;/' /etc/nginx/conf.d/smart-contract-lb.conf
nginx -s reload
sleep 180  # Monitor for 3 minutes

# Check metrics
if ./scripts/check-error-rate.sh; then
    echo "✅ Stage 2 successful, proceeding to stage 3"
else
    echo "❌ Stage 2 failed, rolling back"
    ./scripts/rollback-traffic.sh
    exit 1
fi

# Stage 3: 100% traffic to green
echo "Stage 3: 100% traffic to green"
sed -i 's/server localhost:8000 weight=50;/server localhost:8000 weight=0;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8002 weight=50;/server localhost:8002 weight=100;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8001 weight=50;/server localhost:8001 weight=0;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8003 weight=50;/server localhost:8003 weight=100;/' /etc/nginx/conf.d/smart-contract-lb.conf
nginx -s reload

echo "🎉 Traffic shift completed successfully! Green is now live."
```

### **5. Error Rate Monitoring**
```bash
#!/bin/bash
# scripts/check-error-rate.sh

echo "📊 Checking error rates and performance metrics..."

# Check recent error rates from logs
ERROR_COUNT=$(docker logs unified-main-green --since=5m 2>&1 | grep -c "ERROR\|CRITICAL\|5[0-9][0-9]\|4[0-9][0-9]")
TOTAL_REQUESTS=$(docker logs unified-main-green --since=5m 2>&1 | grep -c "GET\|POST\|PUT\|DELETE")

if [ $TOTAL_REQUESTS -gt 0 ]; then
    ERROR_RATE=$(echo "scale=2; $ERROR_COUNT * 100 / $TOTAL_REQUESTS" | bc -l)
    echo "Error rate: $ERROR_RATE%"
    
    # Fail if error rate > 5%
    if (( $(echo "$ERROR_RATE > 5.0" | bc -l) )); then
        echo "❌ Error rate too high: $ERROR_RATE%"
        exit 1
    fi
fi

# Check response times
AVG_RESPONSE_TIME=$(curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8002/health)
if (( $(echo "$AVG_RESPONSE_TIME > 2.0" | bc -l) )); then
    echo "❌ Response time too slow: ${AVG_RESPONSE_TIME}s"
    exit 1
fi

# Check memory usage
MEMORY_USAGE=$(docker stats unified-main-green --no-stream --format "{{.MemPerc}}" | sed 's/%//')
if (( $(echo "$MEMORY_USAGE > 80.0" | bc -l) )); then
    echo "❌ Memory usage too high: ${MEMORY_USAGE}%"
    exit 1
fi

echo "✅ All metrics within acceptable ranges"
exit 0
```

---

## 🔧 **Integration with CI/CD Pipeline**

### **Enhanced Deployment Stage**
```yaml
deploy:
  name: 🚀 Rolling Deployment
  runs-on: ubuntu-latest
  needs: build
  if: github.ref == 'refs/heads/main'
  environment: production
  
  steps:
  - name: 🟩 Deploy Green Environment
    run: |
      ssh -i ec2-key.pem ec2-user@${{ secrets.EC2_HOST }} "
        cd ~/smart-contract-rewriter/microservices
        docker-compose -f docker-compose.green.yml up -d
        ./scripts/wait-for-green.sh
      "
  
  - name: 🧪 Test Green Environment
    run: |
      ssh -i ec2-key.pem ec2-user@${{ secrets.EC2_HOST }} "
        cd ~/smart-contract-rewriter
        ./scripts/test-green-environment.sh
      "
  
  - name: 🔄 Gradual Traffic Shift
    run: |
      ssh -i ec2-key.pem ec2-user@${{ secrets.EC2_HOST }} "
        cd ~/smart-contract-rewriter
        ./scripts/gradual-traffic-shift.sh
      "
  
  - name: 🟦 Retire Blue Environment
    run: |
      ssh -i ec2-key.pem ec2-user@${{ secrets.EC2_HOST }} "
        cd ~/smart-contract-rewriter/microservices
        docker-compose -f docker-compose.blue.yml down
        docker image prune -f
      "
```

---

## 📊 **Monitoring & Rollback**

### **Automatic Rollback Triggers**
- Error rate > 5%
- Response time > 2 seconds
- Memory usage > 80%
- Health check failures
- Manual trigger via API

### **Rollback Process**
```bash
#!/bin/bash
# scripts/emergency-rollback.sh

echo "🚨 EMERGENCY ROLLBACK INITIATED"

# 1. Immediately switch all traffic back to blue
sed -i 's/server localhost:8000 weight=0;/server localhost:8000 weight=100;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8002 weight=100;/server localhost:8002 weight=0;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8001 weight=0;/server localhost:8001 weight=100;/' /etc/nginx/conf.d/smart-contract-lb.conf
sed -i 's/server localhost:8003 weight=100;/server localhost:8003 weight=0;/' /etc/nginx/conf.d/smart-contract-lb.conf
nginx -s reload

# 2. Stop green environment
docker-compose -f docker-compose.green.yml down

# 3. Verify blue environment health
if curl -f http://localhost:8000/health && curl -f http://localhost:8001/health; then
    echo "✅ Rollback successful - blue environment is healthy"
else
    echo "❌ CRITICAL: Blue environment also unhealthy!"
    # Emergency procedures would go here
fi

echo "🔄 Emergency rollback completed"
```

---

## 🎯 **Key Benefits**

### **Zero-Downtime Deployments**
- ✅ Services remain available during deployment
- ✅ Gradual traffic shifting minimizes risk
- ✅ Instant rollback capability

### **Risk Mitigation**
- ✅ Green environment validation before traffic switch
- ✅ Automated monitoring and rollback
- ✅ Database backup before deployment

### **Operational Excellence**
- ✅ Clear deployment stages and validation
- ✅ Comprehensive monitoring and alerting
- ✅ Automated rollback procedures

---

This rolling deployment strategy ensures enterprise-grade deployment reliability with zero-downtime updates! 🚀
