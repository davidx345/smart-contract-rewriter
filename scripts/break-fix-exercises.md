# 🧪 Phase 3 Break-Fix Exercises

## 🎯 **Learning Objectives**
Practice debugging common CI/CD pipeline failures and build resilience skills.

## 🔥 **Exercise 1: Pipeline Fails in Production but Works in Staging**

### **Scenario Setup:**
```bash
# Simulate environment difference
echo "🔧 Setting up break-fix scenario 1..."

# Create different environment variables
export STAGING_DB_URL="postgresql://user:pass@staging-db:5432/staging_db"
export PRODUCTION_DB_URL="postgresql://user:pass@prod-db:5432/prod_db"

# Different dependency versions
echo "flask==2.0.1" > staging-requirements.txt
echo "flask==2.3.0" > production-requirements.txt
```

### **Problem Symptoms:**
- ✅ Staging pipeline: All tests pass
- ❌ Production pipeline: Deployment fails with dependency conflicts
- ❌ Application crashes with "ModuleNotFoundError"

### **Debugging Steps:**
1. **Check Environment Differences:**
   ```bash
   # Compare environment variables
   diff staging.env production.env
   
   # Check dependency versions
   pip freeze > current-deps.txt
   diff staging-requirements.txt production-requirements.txt
   ```

2. **Identify Root Cause:**
   - Different Python package versions between environments
   - Missing environment variables in production
   - Database connection string format differences

3. **Solution Implementation:**
   ```yaml
   # Add to .github/workflows/ci-cd.yml
   - name: 🔍 Environment Validation
     run: |
       echo "🔍 Validating environment parity..."
       # Check Python version
       python --version
       # Validate required environment variables
       if [[ -z "$DATABASE_URL" ]]; then
         echo "❌ DATABASE_URL not set"
         exit 1
       fi
       # Check critical dependencies
       pip check
   ```

---

## 🔥 **Exercise 2: Security Scan Blocks Deployment**

### **Scenario Setup:**
```bash
# Introduce security vulnerability
echo "requests==2.25.1" >> requirements.txt  # Known vulnerable version
echo "django==3.1.0" >> requirements.txt     # Another vulnerable package

# Add insecure code pattern
cat >> app/main.py << 'EOF'
import subprocess
import os

def execute_command(user_input):
    # SECURITY VULNERABILITY: Command injection
    result = subprocess.run(user_input, shell=True, capture_output=True)
    return result.stdout
EOF
```

### **Problem Symptoms:**
- ❌ Security scan fails with HIGH severity vulnerabilities
- ❌ Deployment blocked by security gate
- ❌ Bandit reports: "Use of subprocess with shell=True"
- ❌ Trivy reports: CVE-2021-33203 in requests library

### **Debugging Steps:**
1. **Analyze Security Reports:**
   ```bash
   # Review Bandit output
   bandit -r . -f json -o bandit-report.json
   cat bandit-report.json | jq '.results[] | {test_name, test_id, issue_severity}'
   
   # Review Trivy output
   trivy fs . --format json --output trivy-report.json
   cat trivy-report.json | jq '.Results[].Vulnerabilities[] | {VulnerabilityID, Severity, PkgName}'
   ```

2. **Fix Security Issues:**
   ```bash
   # Update vulnerable dependencies
   pip install --upgrade requests django
   pip freeze > requirements.txt
   
   # Fix code vulnerability
   sed -i 's/shell=True/shell=False/' app/main.py
   # Add input validation
   ```

3. **Validate Fixes:**
   ```yaml
   # Add security validation step
   - name: 🛡️ Validate Security Fixes
     run: |
       echo "🔍 Re-running security scans..."
       bandit -r . --severity-level medium
       trivy fs . --severity HIGH,CRITICAL --exit-code 1
   ```

---

## 🔥 **Exercise 3: Rolling Deployment Failure**

### **Scenario Setup:**
```bash
# Introduce breaking change that passes tests but fails in production
cat >> app/main.py << 'EOF'
@app.get("/health")
def health_check():
    # Breaking change: This will cause 500 error due to missing import
    return {"status": "healthy", "timestamp": unknown_function()}
EOF
```

### **Problem Symptoms:**
- ✅ All tests pass (tests don't catch runtime error)
- ✅ Deployment starts successfully
- ❌ Health checks fail after deployment
- ❌ Application returns 500 errors
- ✅ Automatic rollback triggers

### **Debugging Steps:**
1. **Monitor Deployment Health:**
   ```bash
   # Check application logs
   docker logs microservices-unified-main --tail 50
   
   # Test health endpoint
   curl -f http://localhost:8000/health || echo "Health check failed"
   ```

2. **Analyze Rollback Process:**
   ```yaml
   - name: 🔄 Automatic Rollback
     if: failure()
     run: |
       echo "🚨 Deployment failed, initiating rollback..."
       git checkout HEAD~1
       docker-compose down
       docker-compose up -d --build
       
       # Verify rollback success
       sleep 30
       curl -f http://localhost:8000/health
   ```

---

## 🔧 **Exercise 4: Container Registry Authentication Failure**

### **Scenario Setup:**
```bash
# Simulate expired registry credentials
unset GITHUB_TOKEN
export REGISTRY_PASSWORD="expired-token"
```

### **Problem Symptoms:**
- ❌ Cannot push images to container registry
- ❌ "Authentication required" errors
- ❌ Deployment fails at image push stage

### **Solution:**
```yaml
- name: 🔐 Login to Container Registry
  uses: docker/login-action@v2
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
    
- name: 🐳 Verify Registry Access
  run: |
    echo "🔍 Testing registry connectivity..."
    docker pull ghcr.io/${{ github.repository }}/test:latest || echo "No existing image found"
```

---

## 📋 **Break-Fix Exercise Checklist**

### **Completed Exercises:**
- [ ] **Environment Parity Debugging** - Fixed staging vs production differences
- [ ] **Security Vulnerability Remediation** - Resolved blocking security issues  
- [ ] **Rolling Deployment Recovery** - Tested automatic rollback mechanisms
- [ ] **Registry Authentication** - Resolved container registry access issues

### **Skills Demonstrated:**
- [ ] **Log Analysis** - Parsed application and pipeline logs
- [ ] **Environment Debugging** - Identified configuration differences
- [ ] **Security Remediation** - Fixed vulnerabilities without breaking functionality
- [ ] **Rollback Procedures** - Executed emergency rollback scenarios
- [ ] **Monitoring Integration** - Set up health checks and alerting

---

## 🎓 **Learning Outcomes**

After completing these exercises, you will have:

1. **Pipeline Resilience** - Your CI/CD pipeline can handle and recover from failures
2. **Security Integration** - Security scanning is properly integrated and blocking dangerous deployments
3. **Environment Parity** - Staging and production environments are properly aligned
4. **Incident Response** - You can quickly debug and resolve deployment issues
5. **Monitoring Skills** - You can effectively monitor and troubleshoot deployments

---

## 🚀 **Next Steps**

1. **Implement monitoring dashboards** for pipeline metrics
2. **Set up alerting** for deployment failures
3. **Create runbooks** for common failure scenarios
4. **Practice chaos engineering** on your deployment infrastructure

These break-fix exercises ensure your Phase 3 CI/CD pipeline is production-ready and resilient! 🏆
