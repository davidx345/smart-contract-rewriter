# DevOps Troubleshooting & Scenarios: Phase 1-6 Guide

Real-world problems and their solutions to deepen your understanding.

---

## Table of Contents

1. [Phase 1-2: Container & Linux Issues](#phase-1-2-container--linux-issues)
2. [Phase 4: VPC & Networking Problems](#phase-4-vpc--networking-problems)
3. [Phase 5: Terraform Disasters](#phase-5-terraform-disasters)
4. [Phase 6: Kubernetes Failures](#phase-6-kubernetes-failures)

---

# Phase 1-2: Container & Linux Issues

## Scenario 1: "Can't SSH to EC2 Instance"

```
ERROR: ssh: connect to host 54.123.45.67 port 22: Connection refused
```

### Root Cause Analysis

```
Possible causes (in order of likelihood):

1. Security Group doesn't allow SSH
   - Instance running, but firewall blocks port 22
   
2. SSH key permissions too open
   - Private key readable by others
   - SSH refuses to use it
   
3. Wrong username for AMI
   - Ubuntu AMI: ubuntu user
   - Amazon Linux: ec2-user user
   - Windows AMI: Administrator user
   
4. Instance doesn't have public IP
   - Running in private subnet
   - Can't access from internet
   
5. Network ACL blocking traffic
   - Subnet-level firewall
   - Blocks inbound or outbound
```

### Debugging Steps

```bash
# Step 1: Check if instance is running
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef \
  --query 'Reservations[0].Instances[0].State.Name'
# Output: running ✓

# Step 2: Check if it has public IP
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef \
  --query 'Reservations[0].Instances[0].PublicIpAddress'
# Output: null or empty = NO PUBLIC IP ✗

# Step 3: Check security group
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef \
  --query 'Reservations[0].Instances[0].SecurityGroups'
# Get security group ID, check its rules:

aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef \
  --query 'SecurityGroups[0].IpPermissions'

# Look for:
# - FromPort: 22
# - ToPort: 22
# - IpProtocol: tcp

# Step 4: Check SSH key permissions
ls -la ~/.ssh/my-key.pem
# Should show: -rw------- (600)
# If not: chmod 600 ~/.ssh/my-key.pem

# Step 5: Try verbose SSH to see what's happening
ssh -vvv -i ~/.ssh/my-key.pem ec2-user@54.123.45.67
# -vvv: triple verbose
# Shows each step of connection process

# Step 6: Try from different machine
# If it works on another machine, your network might be blocking
# (corporate firewall, ISP restrictions, etc.)
```

### Fix

```bash
# Fix 1: Add public IP if missing
aws ec2 associate-address \
  --instance-id i-0123456789abcdef \
  --allocation-id eipalloc-0123456789abcdef

# Fix 2: Update security group to allow SSH
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_IP/32

# Fix 3: Fix SSH key permissions
chmod 600 ~/.ssh/my-key.pem

# Fix 4: Use correct username for AMI
ssh -i ~/.ssh/my-key.pem ubuntu@54.123.45.67  # Ubuntu
ssh -i ~/.ssh/my-key.pem ec2-user@54.123.45.67 # Amazon Linux

# Now try SSH again
ssh -i ~/.ssh/my-key.pem ec2-user@54.123.45.67
```

---

## Scenario 2: "Docker Container Exits Immediately"

```
$ docker run myapp:1.0
[The container exits before you can interact with it]

$ docker logs myapp_container
Error: cannot connect to database
```

### Root Cause Analysis

```
Docker container exited because application crashed
Application crashed because database wasn't available

The issue:
apiVersion: docker-compose.yml

services:
  app:
    image: myapp:1.0
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://db:5432/myapp
  
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password

Problem: App starts before DB is ready!
Docker Compose doesn't automatically wait
```

### Fix

```yaml
# Fixed docker-compose.yml

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://db:5432/myapp
    depends_on:
      db:
        condition: service_healthy  # Wait for health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

# Now app waits for db.service_healthy before starting
```

### Debug Process

```bash
# 1. Check logs
docker logs myapp_container

# 2. Check if container is still running
docker ps
# If not there, it crashed

# 3. See all containers (including stopped)
docker ps -a

# 4. Inspect the exited container
docker inspect myapp_container | grep -A 10 "State"

# 5. Run with /bin/bash to debug
docker run -it myapp:1.0 /bin/bash
# Now you can test manually:
cd /app
python main.py
# See the actual error

# 6. Check environment variables
docker run -it myapp:1.0 env | grep DATABASE
# Make sure DATABASE_URL is set correctly
```

---

# Phase 4: VPC & Networking Problems

## Scenario 3: "Private Subnet Can't Reach Internet"

```
$ ssh -i bastion.pem -J ec2-user@bastion app-user@10.0.2.20
app@app-server:~$ ping 8.8.8.8
# Hangs forever (no response)

app@app-server:~$ curl https://api.github.com
# Connection timeout
```

### Root Cause Analysis

```
Private subnet needs NAT Gateway to reach internet

Check:
1. NAT Gateway exists? (aws ec2 describe-nat-gateways)
2. Private subnet route table points to NAT? (aws ec2 describe-route-tables)
3. NAT Gateway has public IP? (aws ec2 describe-addresses)
4. NAT in correct AZ? (Must be in public subnet same or different AZ)
```

### Debugging

```bash
# 1. Check if NAT Gateway exists
aws ec2 describe-nat-gateways \
  --query 'NatGateways[*].[NatGatewayId,State,PublicIp,SubnetId]'

# Output should show:
# - NatGatewayId: natgw-0123456789abcdef
# - State: available
# - PublicIp: 52.123.45.67
# - SubnetId: subnet-0123456789abcdef (must be public subnet!)

# 2. Check private subnet route table
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-private123 \
  --query 'RouteTables[0].Routes'

# Output should show:
# [{
#   "DestinationCidrBlock": "10.0.0.0/16",
#   "GatewayId": "local"
# },
# {
#   "DestinationCidrBlock": "0.0.0.0/0",
#   "NatGatewayId": "natgw-0123456789abcdef"
# }]

# 3. Check from inside container
ssh -i bastion.pem -J ec2-user@bastion app-user@10.0.2.20

# Once logged in to private instance:
app@app-server:~$ ip route
# Should show:
# default via 10.0.1.1 dev eth0  → via NAT Gateway IP
# 10.0.0.0/16 dev eth0 scope link → local network

app@app-server:~$ traceroute 8.8.8.8
# Shows path to destination
# First hop should be NAT gateway
```

### Fix

```bash
# If NAT Gateway doesn't exist, create it
# 1. Create Elastic IP
ALLOC_ID=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
echo $ALLOC_ID

# 2. Create NAT Gateway in public subnet
NAT_GW=$(aws ec2 create-nat-gateway \
  --subnet-id subnet-public123 \
  --allocation-id $ALLOC_ID \
  --query 'NatGateway.NatGatewayId' \
  --output text)
echo $NAT_GW

# Wait for NAT to be available
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW

# 3. Update private subnet route table
ROUTE_TABLE=$(aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-private123 \
  --query 'RouteTables[0].RouteTableId' --output text)

aws ec2 create-route \
  --route-table-id $ROUTE_TABLE \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW

# Now test again from private instance
ssh -i bastion.pem -J ec2-user@bastion app-user@10.0.2.20
app@app-server:~$ ping 8.8.8.8
# Should work!
```

---

## Scenario 4: "Can't SSH to Private Subnet from Bastion"

```
$ ssh -i bastion.pem -J ec2-user@54.123.45.67 ubuntu@10.0.2.20
# Hangs forever or: Connection refused
```

### Root Cause Analysis

```
Check:
1. Bastion security group allows outbound SSH to private subnet?
2. Private instance security group allows inbound SSH from bastion?
3. Network ACL on both subnets allow port 22?
4. Private instance has SSH daemon running?
5. Route between subnets exists?
```

### Debugging

```bash
# From bastion (after SSH into it):
ec2-user@bastion:~$ ssh -vvv ubuntu@10.0.2.20
# -vvv shows where it hangs

# Check if port is open on private instance
ec2-user@bastion:~$ nc -zv 10.0.2.20 22
# Connection refused = port not listening
# Timeout = firewall blocking

# From local machine, check security groups
aws ec2 describe-security-groups \
  --group-ids sg-bastion sg-private-app \
  --query 'SecurityGroups[*].[GroupId,IpPermissions]'

# Bastion SG should have egress rule:
# "IpProtocol": "tcp",
# "FromPort": 22,
# "ToPort": 22,
# "IpRanges": [{"CidrIp": "10.0.2.0/24"}]

# Private app SG should have ingress rule:
# "IpProtocol": "tcp",
# "FromPort": 22,
# "ToPort": 22,
# "UserIdGroupPairs": [{"GroupId": "sg-bastion"}]  ← From bastion SG!
```

### Fix

```bash
# Update bastion security group (allow outbound SSH to private)
aws ec2 authorize-security-group-egress \
  --group-id sg-bastion \
  --protocol tcp \
  --port 22 \
  --cidr 10.0.2.0/24

# Update private app security group (allow inbound SSH from bastion)
aws ec2 authorize-security-group-ingress \
  --group-id sg-private-app \
  --protocol tcp \
  --port 22 \
  --source-group sg-bastion

# Now try again
ssh -i bastion.pem -J ec2-user@54.123.45.67 ubuntu@10.0.2.20
# Should work!
```

---

# Phase 5: Terraform Disasters

## Scenario 5: "Terraform State is Corrupted"

```
$ terraform plan
Error: aws_security_group.bastion: invalid instance ID

But the security group exists in AWS!
```

### Root Cause Analysis

```
State file (.tfstate JSON) and AWS reality are out of sync

Causes:
1. Someone manually created/deleted resources in console
2. State file got corrupted
3. Different person applied terraform without pulling latest state
4. S3 state backend issue
```

### Recovery

```bash
# 1. Check state file
terraform state list
# Shows all resources in state

terraform state show aws_security_group.bastion
# Shows current state of resource

# 2. Check AWS reality
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef \
  --query 'SecurityGroups[0]'

# 3. If they don't match, refresh state
terraform refresh
# Syncs state with AWS

# 4. If state is truly corrupted, rebuild it
# WARNING: Only if you understand consequences!

# Option 1: Import existing resource
terraform import aws_security_group.bastion sg-0123456789abcdef
# Updates state to match reality

# Option 2: Remove and re-import
terraform state rm aws_security_group.bastion
terraform import aws_security_group.bastion sg-0123456789abcdef

# Option 3: Manual state edit (dangerous!)
terraform state pull > backup.json  # Backup first!
# Edit backup.json to fix the issue
terraform state push backup.json

# Now plan again
terraform plan
```

---

## Scenario 6: "Terraform Destroy Deletes Database!"

```
$ terraform destroy -auto-approve
# ... resources being destroyed ...
# aws_db_instance.postgres destroyed!

OH NO! The database was deleted!
```

### Prevention

```hcl
# Add protection to critical resources

resource "aws_db_instance" "postgres" {
  allocated_storage       = 100
  db_instance_class       = "db.t3.micro"
  engine                  = "postgres"
  identifier              = "production-db"
  skip_final_snapshot     = false  # ← Always take snapshot before delete
  final_snapshot_identifier = "production-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "production-database"
    Environment = "production"
  }
}

# Now if you try to destroy:
$ terraform destroy
Error: resource "aws_db_instance.postgres" has protect_destroy set

# Force delete (very intentional):
terraform destroy -var='allow_destroy=true'
```

### Recovery if Deleted

```bash
# AWS keeps final snapshots for a while

# List snapshots
aws rds describe-db-snapshots \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,CreateTime]'

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier production-db-restored \
  --db-snapshot-identifier production-db-final-snapshot-2025-10-24-1234

# This creates a new database from the snapshot
# You'll have all your data back!

# Then import back into Terraform:
terraform import aws_db_instance.postgres production-db-restored
```

---

# Phase 6: Kubernetes Failures

## Scenario 7: "Pod Won't Start - CrashLoopBackOff"

```
$ kubectl get pods
NAME                    READY   STATUS             RESTARTS   AGE
backend-deployment-1    0/1     CrashLoopBackOff   5          2m

$ kubectl logs backend-deployment-1
[ERROR] Cannot connect to database: connection refused
```

### Root Cause Analysis

```
Pod keeps restarting because application crashes
Container crashes because it can't connect to database

Possible causes:
1. Database not running
2. Database not reachable (network issue)
3. Wrong connection string (env vars)
4. Database password incorrect
5. Port blocked by security group
6. Pod DNS not resolving service name
```

### Debugging

```bash
# 1. Check pod status
kubectl describe pod backend-deployment-1 -n default

# Look for:
# - State: Running/CrashLoopBackOff
# - Container ID: Should be present
# - Restarts: Shows how many times it crashed
# - Last State: Why it exited

# 2. Check logs
kubectl logs backend-deployment-1 -n default
# Last crash logs

kubectl logs backend-deployment-1 --previous
# Logs from before previous restart

# 3. Check if database pod is running
kubectl get pods -n default
# Should see database pod in Running state

# 4. Check service discovery
kubectl get svc -n default
# database-service should exist

# 5. Try to ping database from app pod
kubectl exec -it backend-deployment-1 -- sh
# Now inside the pod:
app@pod:~$ ping database-service
# Should resolve to IP

app@pod:~$ telnet database-service 5432
# Should connect to database

# 6. Check environment variables in pod
kubectl set env pod/backend-deployment-1 --list
# See what env vars the pod has

# 7. Check if resource limits are causing issues
kubectl describe pod backend-deployment-1
# Look for: OOMKilled (out of memory)
```

### Fix

```bash
# Fix 1: Ensure database is running
kubectl get statefulsets -n default
kubectl describe statefulset postgres

# If not running:
kubectl rollout restart statefulset/postgres

# Fix 2: Check service connectivity
kubectl get svc -n default
kubectl get endpoints database-service

# If no endpoints, pods aren't running
# Fix 3: Update environment variables
kubectl set env deployment/backend \
  DATABASE_URL=postgresql://postgres:password@database-service:5432/mydb

# This triggers rollout of new pods with correct env vars

# Fix 4: Check resource requests/limits
kubectl describe node

# If node out of resources, delete other pods or add nodes

# Fix 5: Update deployment with new container
kubectl set image deployment/backend \
  backend=myapp:1.1 --record

# Triggers rolling update with new image
# --record: saves this action in rollout history

# Monitor rollout
kubectl rollout status deployment/backend

# If the new version still crashes, rollback
kubectl rollout undo deployment/backend
```

---

## Scenario 8: "Service Can't Reach Backend Pods"

```
Frontend pod tries to connect to backend service:
curl http://backend-service:8000/health

ERROR: Connection refused
```

### Debugging

```bash
# 1. Check service exists
kubectl get svc backend-service
# Should show CLUSTER-IP

# 2. Check endpoints (which pods it routes to)
kubectl get endpoints backend-service
# Should show IP addresses of backend pods

# If empty: No pods match the selector!

# 3. Check pod labels
kubectl get pods --show-labels
# backend pods should have: app=backend

# 4. Check service selector
kubectl describe svc backend-service
# Selector: app=backend

# If selector doesn't match pod labels, no connection!

# 5. Test connectivity from frontend pod
kubectl exec -it frontend-pod -- sh
frontend@pod:~$ curl -v http://backend-service:8000/health

# 6. Check network policies
kubectl get networkpolicies -n default
# Check if they block frontend → backend

# 7. Check DNS
kubectl exec -it frontend-pod -- nslookup backend-service
# Should resolve to service IP
```

### Fix

```bash
# Fix 1: Add matching labels to backend pods
kubectl label pods backend-pod-1 app=backend
kubectl label pods backend-pod-2 app=backend

# Or update deployment:
kubectl set selector deployment/backend "app=backend"

# Fix 2: Create/update network policy to allow traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000

# Apply it
kubectl apply -f network-policy.yaml

# Now test again
kubectl exec -it frontend-pod -- curl http://backend-service:8000/health
# Should work!
```

---

## Scenario 9: "Out of Disk Space in Cluster"

```
$ kubectl get nodes
NAME       STATUS   ROLES    AGE   VERSION
node-1     NotReady   worker   30d   v1.28.0

$ kubectl describe node node-1
DiskPressure: True
```

### Debugging

```bash
# 1. Check disk usage on node
kubectl debug node/node-1 -it --image=ubuntu

# Inside the debug container:
root@node-1:~# df -h /
# Shows disk usage

# 2. Check what's taking space
root@node-1:~# du -sh /var/lib/docker/*
# Docker images and containers

root@node-1:~# du -sh /var/lib/kubelet/pods/*
# Pod storage

# 3. Check for stuck containers
docker ps -a | grep -v Running
# Shows stopped containers still using space

# 4. Find large files
root@node-1:~# find / -size +1G -type f 2>/dev/null
# Files larger than 1GB
```

### Fix

```bash
# Fix 1: Clean up Docker resources
docker system prune -a --volumes
# Removes:
# - Stopped containers
# - Unused images
# - Unused volumes

# Fix 2: Add more disk
# Increase EBS volume size and extend filesystem

# Fix 3: Limit pod storage
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    resources:
      requests:
        ephemeralStorage: 1Gi
      limits:
        ephemeralStorage: 2Gi

# Pod can only use up to 2Gi of disk

# Fix 4: Add more worker nodes
terraform apply -var="node_count=5"
# Scales cluster to 5 nodes

# Fix 5: Evict pods from full node
kubectl drain node-1 --ignore-daemonsets
# Moves all pods to other nodes

# Now fix the node and add back
kubectl uncordon node-1
```

---

## Scenario 10: "Helm Chart Deployment Failed"

```
$ helm install backend ./backend-chart
ERROR: failed to create resource: secrets "backend-secret" already exists
```

### Debugging

```bash
# 1. Check if release exists
helm list
# If it shows the release, it might be stuck

helm get values backend
# See current values

# 2. Check deployment
kubectl get deployment backend
kubectl describe deployment backend

# 3. Check secrets
kubectl get secrets
kubectl describe secret backend-secret

# 4. Check previous releases
helm history backend
# Shows all versions installed
```

### Fix

```bash
# Fix 1: Delete the failed release
helm delete backend
# Removes all resources

# Then reinstall
helm install backend ./backend-chart

# Fix 2: Use helm upgrade instead
helm upgrade --install backend ./backend-chart
# If release exists, upgrades it
# If not, creates it

# Fix 3: If secret is already there, skip recreating
helm install backend ./backend-chart \
  --set skipCreateSecret=true

# Fix 4: Clean up everything and start fresh
kubectl delete all --all
helm delete backend
kubectl delete pvc --all

# Now reinstall from scratch
helm install backend ./backend-chart
```

---

## Summary of Debugging Principles

```
1. GATHER INFORMATION
   - Check logs (kubectl logs, docker logs)
   - Check status (kubectl get, aws ec2 describe)
   - Check configuration (kubectl describe, terraform state show)

2. COMPARE EXPECTED vs ACTUAL
   - What should happen vs what's happening
   - Configuration vs reality
   - State file vs AWS

3. ISOLATE THE PROBLEM
   - Is it network? (try connectivity)
   - Is it configuration? (check env vars)
   - Is it resource? (check disk, memory, CPU)
   - Is it permission? (check IAM, RBAC)

4. TEST THE FIX
   - Don't just apply blindly
   - Test in dev first
   - Verify it works before production

5. DOCUMENT THE SOLUTION
   - Why it happened
   - How you fixed it
   - How to prevent it next time
```

---

## Common Tools and Commands

```bash
# AWS / VPC Debugging
aws ec2 describe-instances --query 'Reservations[0].Instances[0]'
aws ec2 describe-security-groups --group-ids sg-xyz
aws ec2 describe-route-tables --filters Name=vpc-id,Values=vpc-xyz
aws ec2 describe-nat-gateways --query 'NatGateways[*]'

# SSH / Bastion Debugging
ssh -vvv user@host          # Very verbose
ssh -J jump-host app-host   # Jump through bastion
ssh -L 5432:db-host:5432    # Port forward

# Terraform Debugging
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
terraform state list
terraform state show resource_name
terraform graph                         # Visualize dependencies

# Docker Debugging
docker logs container-name
docker exec -it container /bin/bash
docker inspect container-name
docker stats                            # Resource usage

# Kubernetes Debugging
kubectl get all -n default
kubectl describe pod pod-name
kubectl logs pod-name --previous
kubectl exec -it pod-name -- sh
kubectl get events -n default --sort-by='.lastTimestamp'
kubectl port-forward svc/service 8000:8000  # Local access
```

This is real DevOps work!
