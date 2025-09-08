# 🔧 Pipeline Troubleshooting Guide

## 🚨 **Quick Diagnosis Commands**

### **Pipeline Status Check:**
```bash
# Check GitHub Actions status
gh workflow list
gh run list --limit 5

# Check AWS deployment
aws ec2 describe-instances --instance-ids i-094945951ee1c0a0d --query 'Reservations[].Instances[].{State:State.Name,PublicIP:PublicIpAddress}'

# Test live services
curl -f http://3.87.248.104:8000/health
```

---

## 🔍 **Common Pipeline Failures & Solutions**

### **1. Test Stage Failures**

#### **Problem: Tests failing on dependencies**
```yaml
❌ Error: ModuleNotFoundError: No module named 'pytest'
```

**Solution:**
```yaml
- name: 📦 Install Dependencies
  run: |
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install pytest pytest-asyncio httpx  # Add missing test deps
```

#### **Problem: Database connection in tests**
```yaml
❌ Error: could not connect to server: Connection refused
```

**Solution:**
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_PASSWORD: testpass123
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 5432:5432
```

---

### **2. Security Scan Failures**

#### **Problem: High severity vulnerabilities found**
```bash
❌ CRITICAL: CVE-2023-12345 found in package 'requests'
```

**Solution:**
```bash
# Update vulnerable packages
pip install --upgrade requests urllib3 flask
pip freeze > requirements.txt

# Re-run security scan
bandit -r . --severity-level medium
trivy fs . --severity HIGH,CRITICAL
```

#### **Problem: Code security issues**
```bash
❌ B602: Use of subprocess with shell=True
```

**Solution:**
```python
# Bad:
subprocess.run(user_input, shell=True)

# Good:  
subprocess.run(user_input.split(), shell=False)
```

---

### **3. Build Stage Failures**

#### **Problem: Docker build failures**
```bash
❌ Error: failed to solve: dockerfile parse error
```

**Solution:**
```dockerfile
# Check Dockerfile syntax
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Correct port exposure
EXPOSE 8000

# Valid CMD syntax
CMD ["python", "unified_main.py"]
```

#### **Problem: Container registry authentication**
```bash
❌ Error: unauthorized: authentication required
```

**Solution:**
```yaml
- name: 🔐 Login to Container Registry
  uses: docker/login-action@v2
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

---

### **4. Deployment Stage Failures**

#### **Problem: AWS connection issues**
```bash
❌ Error: Unable to locate credentials
```

**Solution:**
```yaml
- name: 🔧 Setup AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ secrets.AWS_REGION }}
```

#### **Problem: SSH connection to EC2 fails**
```bash
❌ Error: Permission denied (publickey)
```

**Solution:**
```yaml
- name: 🔑 Setup SSH Key
  run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.EC2_PRIVATE_KEY }}" > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -H ${{ secrets.EC2_HOST }} >> ~/.ssh/known_hosts
```

#### **Problem: Docker Compose fails on EC2**
```bash
❌ Error: service 'unified-main' failed to build
```

**Solution:**
```bash
# SSH to EC2 and debug
ssh -i key.pem ec2-user@3.87.248.104

# Check Docker status
docker ps
docker-compose logs

# Manual rebuild
docker-compose down
docker-compose up -d --build

# Check logs
docker logs microservices-unified-main
```

---

### **5. Health Check Failures**

#### **Problem: Service not responding**
```bash
❌ Health check failed: Connection refused
```

**Debug Steps:**
```bash
# Check if containers are running
docker ps

# Check container logs
docker logs microservices-unified-main --tail 50

# Check port binding
netstat -tlnp | grep 8000

# Test from inside container
docker exec -it microservices-unified-main curl localhost:8000/health
```

**Solution:**
```python
# Ensure health endpoint exists
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Ensure app runs on correct host
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Not 127.0.0.1
```

---

## 🔧 **GitHub Secrets Troubleshooting**

### **Required Secrets Checklist:**
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# EC2 Details
EC2_HOST=3.87.248.104
EC2_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----...

# Application Secrets
GEMINI_API_KEY=AIza...
SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://...
```

### **Secrets Validation:**
```yaml
- name: 🔍 Validate Secrets
  run: |
    if [[ -z "${{ secrets.AWS_ACCESS_KEY_ID }}" ]]; then
      echo "❌ AWS_ACCESS_KEY_ID not set"
      exit 1
    fi
    echo "✅ Required secrets are configured"
```

---

## 🚨 **Emergency Procedures**

### **Pipeline Stuck/Hanging:**
```bash
# Cancel running workflow
gh run cancel <run-id>

# Force restart
gh workflow run ci-cd.yml
```

### **Deployment Rollback:**
```bash
# Manual rollback on EC2
ssh -i key.pem ec2-user@3.87.248.104
cd ~/smart-contract-rewriter/microservices
git checkout HEAD~1
docker-compose down
docker-compose up -d --build
```

### **Complete Environment Reset:**
```bash
# Reset EC2 deployment
ssh -i key.pem ec2-user@3.87.248.104
docker-compose down -v  # Remove volumes
docker system prune -a  # Clean images
git pull origin main
docker-compose up -d --build
```

---

## 📊 **Monitoring Commands**

### **Pipeline Health:**
```bash
# Recent pipeline runs
gh run list --limit 10

# Detailed run information
gh run view <run-id>

# Download logs
gh run download <run-id>
```

### **Application Health:**
```bash
# Service status
curl -f http://3.87.248.104:8000/health

# Performance check
time curl -s http://3.87.248.104:8000/health

# Detailed API check
curl -s http://3.87.248.104:8000/ | jq
```

---

## 🎯 **Troubleshooting Workflow**

1. **🔍 Identify Stage** - Which pipeline stage failed?
2. **📋 Check Logs** - Review GitHub Actions logs
3. **🔧 Isolate Issue** - Test individual components
4. **💡 Apply Fix** - Use solutions from this guide
5. **✅ Validate** - Confirm fix works
6. **📚 Document** - Add to troubleshooting guide

---

## 🆘 **Getting Help**

### **Log Collection:**
```bash
# Collect all relevant logs
mkdir troubleshooting-$(date +%Y%m%d)
cd troubleshooting-$(date +%Y%m%d)

# GitHub Actions logs
gh run download <latest-run-id>

# EC2 logs
ssh -i key.pem ec2-user@3.87.248.104 "docker-compose logs" > docker-logs.txt

# System info
aws ec2 describe-instances --instance-ids i-094945951ee1c0a0d > instance-info.json
```

### **Support Channels:**
- 📚 **Documentation**: Check AWS-MIGRATION-SUMMARY.md
- 🧪 **Testing**: Run break-fix-exercises.md scenarios
- 🔍 **Debugging**: Use aws-monitoring.py for real-time monitoring

---

This troubleshooting guide covers 95% of common pipeline issues. Keep it bookmarked for quick reference! 🚀
