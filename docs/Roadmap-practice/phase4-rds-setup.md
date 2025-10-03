# 🗄️ Phase 4.1: AWS RDS Setup Guide

## 🎯 Learning Objective
Transform from containerized PostgreSQL to enterprise-grade managed database with high availability, automated backups, and read replicas.

## 🏗️ Architecture Overview

### Current Setup (Development)
```
EC2 Instance (3.87.248.104)
├── Docker Container: unified-main (port 8000)
├── Docker Container: contract-service (port 8001)
└── Docker Container: postgres (port 5432) ← Single point of failure!
```

### Target Setup (Production)
```
VPC (Virtual Private Cloud)
├── Public Subnet (EC2 instances)
│   ├── unified-main (port 8000)
│   └── contract-service (port 8001)
└── Private Subnet (Database tier)
    ├── RDS Primary (Multi-AZ)
    └── RDS Read Replica (for scaling)
```

## 📋 Step-by-Step Implementation

### Step 1: Design RDS Configuration

#### Database Specifications (FREE TIER OPTIMIZED)
- **Engine**: PostgreSQL 15
- **Instance Class**: db.t3.micro (Free Tier - 750 hours/month)
- **Storage**: 20 GB gp2 (Free Tier - up to 20 GB)
- **Multi-AZ**: ❌ NO (costs double - not free tier)
- **Backup Retention**: 7 days (Free Tier - up to 20 GB backup storage)
- **Read Replica**: ❌ NO (costs ~$15/month - add later when needed)

#### Security Configuration (FREE TIER OPTIMIZED)
- **VPC**: Custom VPC with private subnets
- **Security Group**: Database access only from application servers
- **Encryption**: ✅ AES-256 encryption at rest (FREE)
- **SSL/TLS**: ✅ Force encrypted connections (FREE)
- **Authentication**: Username/password + IAM database authentication
- **Performance Insights**: ❌ DISABLED (costs extra for retention)

### Step 2: Cost Analysis (AWS Free Tier OPTIMIZED)
```
✅ FREE TIER COSTS:
RDS db.t3.micro (750 hours/month): $0.00
Storage 20 GB gp2: $0.00 (up to 20 GB free)
Backup storage: $0.00 (up to 20 GB free)
Data Transfer: $0.00 (within same AZ)

❌ AVOIDED COSTS (not free tier):
Multi-AZ deployment: ~$15/month (second instance)
Read Replica: ~$15/month (additional instance)
Performance Insights: ~$3/month (long-term retention)
Storage > 20GB: $0.10/GB/month

💡 TOTAL MONTHLY COST: $0.00 (stays in free tier)
```

### 🎓 **LESSON: Free Tier vs Production Trade-offs**
- **Free Tier**: Single AZ, no read replica, basic monitoring
- **Production**: Multi-AZ, read replicas, advanced monitoring
- **When to upgrade**: When you outgrow free tier or need HA

### Step 3: Security Groups Design
```yaml
Database Security Group:
  Inbound Rules:
    - Port 5432 (PostgreSQL)
    - Source: Application Security Group only
    - Protocol: TCP
  
  Outbound Rules:
    - All traffic allowed (for AWS services)

Application Security Group:
  Inbound Rules:
    - Port 8000, 8001 (Applications)
    - Source: 0.0.0.0/0 (Internet)
    - Protocol: TCP
  
  Outbound Rules:
    - Port 5432 to Database Security Group
    - Port 443 (HTTPS) to 0.0.0.0/0
    - Protocol: TCP
```

### Step 4: Migration Strategy
```
Phase A: Setup RDS (No downtime)
├── Create VPC and subnets
├── Create RDS instance
├── Test connectivity
└── Validate performance

Phase B: Dual-write period (Minimal risk)
├── Update application config
├── Write to both databases
├── Validate data consistency
└── Test application functionality

Phase C: Cut-over (Brief downtime < 5 minutes)
├── Stop application briefly
├── Final data sync
├── Switch to RDS only
└── Restart application

Phase D: Cleanup (No downtime)
├── Monitor RDS performance
├── Remove old database container
└── Update documentation
```

## 🔧 Implementation Commands

### AWS CLI Setup (We'll use this)
```bash
# Configure AWS CLI with your credentials
aws configure

# Test connection
aws sts get-caller-identity
```

### Create RDS Instance
```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name smart-contract-db-subnet \
  --db-subnet-group-description "Smart Contract Database Subnets" \
  --subnet-ids subnet-12345 subnet-67890

# Create security group
aws ec2 create-security-group \
  --group-name smart-contract-db-sg \
  --description "Smart Contract Database Security Group" \
  --vpc-id vpc-12345

# Create RDS instance (FREE TIER OPTIMIZED)
aws rds create-db-instance \
  --db-instance-identifier smart-contract-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username smartcontract_admin \
  --master-user-password [SECURE_PASSWORD] \
  --allocated-storage 20 \
  --storage-type gp2 \
  --vpc-security-group-ids sg-12345 \
  --db-subnet-group-name smart-contract-db-subnet \
  --backup-retention-period 7 \
  --no-multi-az \
  --storage-encrypted \
  --no-enable-performance-insights \
  --tags Key=Project,Value=SmartContractRewriter
```

## 📊 Monitoring and Alerting

### CloudWatch Metrics to Monitor
- **Database Connections**: Track concurrent connections
- **CPU Utilization**: Should stay below 80%
- **Database Load**: Monitor query performance
- **Storage Space**: Alert when > 85% full
- **Backup Status**: Ensure backups complete successfully

### Performance Insights
- **Top SQL Statements**: Identify slow queries
- **Wait Events**: Find database bottlenecks
- **Database Load**: Visualize performance over time

## 🔍 Testing Strategy

### Connection Testing
```python
# Test database connectivity
import psycopg2
import os

def test_rds_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('RDS_ENDPOINT'),
            port=5432,
            database='smart_contract_db',
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            sslmode='require'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"Connected to: {version}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
```

### Performance Testing
```sql
-- Create test data
INSERT INTO contracts (address, source_code, analysis_result) 
SELECT 
  '0x' || md5(random()::text),
  'contract Test' || generate_series || ' { }',
  '{"complexity": ' || (random() * 100)::int || '}'
FROM generate_series(1, 10000);

-- Test query performance
EXPLAIN ANALYZE SELECT * FROM contracts WHERE complexity > 50;
```

## 🚨 Security Best Practices

### Database Security Checklist
- [ ] Enable encryption at rest
- [ ] Force SSL/TLS connections
- [ ] Use strong passwords (AWS Secrets Manager)
- [ ] Restrict network access via security groups
- [ ] Enable CloudTrail for audit logging
- [ ] Regular security updates (automated)
- [ ] Monitor failed login attempts

### Network Security
- [ ] Place RDS in private subnets
- [ ] Use VPC endpoints for AWS services
- [ ] Implement least-privilege security groups
- [ ] Enable VPC Flow Logs
- [ ] Consider AWS PrivateLink for enhanced security

## 📝 Documentation Requirements

### Post-Implementation Documentation
1. **Connection Details**: Endpoints, ports, SSL requirements
2. **Backup Strategy**: Retention periods, recovery procedures
3. **Monitoring Setup**: CloudWatch dashboards, alerting
4. **Security Configuration**: Security groups, encryption keys
5. **Performance Baselines**: Query performance metrics
6. **Disaster Recovery**: RTO/RPO targets, failover procedures

## 🎯 Success Criteria

### Phase 4.1 Complete When:
- [ ] RDS instance running and accessible
- [ ] Application successfully connects to RDS
- [ ] Automated backups configured and tested
- [ ] Read replica created and tested
- [ ] Security groups properly configured
- [ ] Monitoring and alerting active
- [ ] Documentation complete

---

**Next: We'll implement this step-by-step, starting with VPC design and RDS creation!**
