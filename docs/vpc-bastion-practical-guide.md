# VPC & Bastion Host: Practical Deep Dive

A comprehensive guide with practical examples and visual diagrams for understanding VPCs, subnets, and bastion hosts.

---

## Table of Contents

1. [Complete VPC Architecture Example](#complete-vpc-architecture-example)
2. [Bastion Host Practical Guide](#bastion-host-practical-guide)
3. [Real-World Scenarios](#real-world-scenarios)
4. [Security Implementation](#security-implementation)

---

## Complete VPC Architecture Example

### Simple 3-Tier VPC Setup

```
┌────────────────────────────────────────────────────────────────────────┐
│  AWS Region: us-east-1                                                  │
│  VPC: 10.0.0.0/16 (65,536 IP addresses)                                 │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Availability Zone: us-east-1a                                  │  │
│  │                                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────┐   │  │
│  │  │  PUBLIC SUBNET: 10.0.1.0/24 (256 IPs, 251 usable)      │   │  │
│  │  │  - Internet-facing                                      │   │  │
│  │  │  - Bastion host lives here                              │   │  │
│  │  │                                                         │   │  │
│  │  │  ┌────────────────────────────────────────────────┐    │   │  │
│  │  │  │ Bastion Host (Jump Server)                     │    │   │  │
│  │  │  │ Private IP: 10.0.1.10                          │    │   │  │
│  │  │  │ Public IP: 52.123.45.67                        │    │   │  │
│  │  │  │ Security Group:                                │    │   │  │
│  │  │  │  - Inbound: SSH (22) from YOUR_IP only        │    │   │  │
│  │  │  │  - Outbound: SSH (22) to 10.0.2.0/24         │    │   │  │
│  │  │  │  - Outbound: SSH (22) to 10.0.3.0/24         │    │   │  │
│  │  │  │  - NO internet access (no HTTP/HTTPS)         │    │   │  │
│  │  │  └────────────────────────────────────────────────┘    │   │  │
│  │  └─────────────────────────────────────────────────────────┘   │  │
│  │           ↑                                                     │  │
│  │           │ SSH from Internet                                   │  │
│  │           │ 52.123.45.67:22                                    │  │
│  │                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────┐   │  │
│  │  │  PRIVATE SUBNET (Application): 10.0.2.0/24             │   │  │
│  │  │  - No direct internet access                           │   │  │
│  │  │  - Can reach internet through NAT gateway              │   │  │
│  │  │                                                         │   │  │
│  │  │  ┌────────────────────────────────────────────────┐    │   │  │
│  │  │  │ Backend Application Server                     │    │   │  │
│  │  │  │ Private IP: 10.0.2.20                          │    │   │  │
│  │  │  │ NO public IP                                   │    │   │  │
│  │  │  │ Security Group:                                │    │   │  │
│  │  │  │  - Inbound: SSH (22) from 10.0.1.0/24 (bastion)│   │   │  │
│  │  │  │  - Inbound: HTTP (8000) from 10.0.0.0/16      │    │   │  │
│  │  │  │  - Outbound: All traffic through NAT           │    │   │  │
│  │  │  └────────────────────────────────────────────────┘    │   │  │
│  │  └─────────────────────────────────────────────────────────┘   │  │
│  │           ↑                                                     │  │
│  │           │ SSH from Bastion                                   │  │
│  │           │ (internal network)                                 │  │
│  │                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────┐   │  │
│  │  │  PRIVATE SUBNET (Database): 10.0.3.0/24               │   │  │
│  │  │  - Completely isolated                                 │   │  │
│  │  │  - Only reachable from app subnet                      │   │  │
│  │  │  - No internet access                                  │   │  │
│  │  │                                                         │   │  │
│  │  │  ┌────────────────────────────────────────────────┐    │   │  │
│  │  │  │ PostgreSQL Database                           │    │   │  │
│  │  │  │ Private IP: 10.0.3.30                          │    │   │  │
│  │  │  │ Security Group:                                │    │   │  │
│  │  │  │  - Inbound: PostgreSQL (5432) from 10.0.2.0/24│    │   │  │
│  │  │  │  - Inbound: SSH (22) from 10.0.1.0/24 (bastion)│   │   │  │
│  │  │  │  - NO outbound (only responds)                │    │   │  │
│  │  │  └────────────────────────────────────────────────┘    │   │  │
│  │  └─────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Internet Gateway                                               │  │
│  │  Provides route to internet                                    │  │
│  │  0.0.0.0/0 → IGW                                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│           ↑                                                              │
│           │                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  NAT Gateway                                                     │  │
│  │  Private IPs can reach internet                                 │  │
│  │  10.0.2.x → NAT (52.xxx.xxx.x) → Internet                      │  │
│  │  Response → NAT → 10.0.2.x                                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│           ↑                                                              │
│           │                                                              │
│        Internet                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### IP Address Allocation

```
VPC CIDR: 10.0.0.0/16
Total addresses: 65,536

Public Subnet: 10.0.1.0/24
├─ 10.0.1.0         Reserved (network)
├─ 10.0.1.1         Reserved (router)
├─ 10.0.1.2         Reserved (DNS)
├─ 10.0.1.3         Reserved (future)
├─ 10.0.1.4-10.0.1.254   Available (251 IPs)
│  ├─ 10.0.1.10     Bastion host
│  ├─ 10.0.1.11-254 Available for more servers
└─ 10.0.1.255       Reserved (broadcast)

Private Subnet (App): 10.0.2.0/24
├─ 10.0.2.0         Reserved
├─ 10.0.2.1         Reserved
├─ 10.0.2.2         Reserved
├─ 10.0.2.3         Reserved
├─ 10.0.2.4-10.0.2.254   Available (251 IPs)
│  ├─ 10.0.2.20     Backend app server 1
│  ├─ 10.0.2.21     Backend app server 2
│  ├─ 10.0.2.22     Backend app server 3
│  └─ 10.0.2.23-254 Available for scaling
└─ 10.0.2.255       Reserved

Private Subnet (DB): 10.0.3.0/24
├─ 10.0.3.0-10.0.3.3 Reserved
├─ 10.0.3.4-10.0.3.254 Available (251 IPs)
│  ├─ 10.0.3.30     PostgreSQL primary
│  ├─ 10.0.3.31     PostgreSQL replica
│  └─ 10.0.3.32-254 Available
└─ 10.0.3.255       Reserved
```

---

## Bastion Host Practical Guide

### Why You Need a Bastion Host

```
Scenario 1: Without Bastion Host (INSECURE)
┌──────────────────────────────────────────┐
│ Private Database (10.0.3.30)             │
│ Public IP: 52.200.1.1                    │
│ Security Group: SSH from 0.0.0.0/0       │
└──────────────────────────────────────────┘
           ↑
      EXPOSED TO INTERNET!
           
Anyone on the internet can try to SSH:
ssh -i guessed-key.pem ubuntu@52.200.1.1

If password weak or key compromised:
- Direct access to database
- Steal all data
- Modify data
- Delete everything


Scenario 2: With Bastion Host (SECURE)
┌─────────────────────────────────┐
│ Bastion Host (10.0.1.10)        │
│ Public IP: 54.123.45.67         │
│ Security Group:                 │
│  - SSH only from YOUR_IP        │
│ NO database access              │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│ Private Database (10.0.3.30)    │
│ NO public IP                    │
│ Security Group:                 │
│  - SSH from Bastion only        │
│ Hidden from internet            │
└─────────────────────────────────┘

Attacker on internet:
- Can find Bastion (public IP)
- Can't SSH (not their IP)
- Blocked at security group
- Even if they get in, can't reach database
```

### Setting Up Bastion Host

#### Terraform Code

```hcl
# Create key pair for bastion
resource "aws_key_pair" "bastion_key" {
  key_name   = "bastion-key"
  public_key = file("~/.ssh/bastion_key.pub")
}

# Security group for bastion
resource "aws_security_group" "bastion_sg" {
  name        = "bastion-security-group"
  description = "Security group for bastion host"
  vpc_id      = aws_vpc.main.id

  # Only your IP can SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["YOUR_IP/32"]  # Replace with your IP
    # Example: "203.0.113.45/32"
  }

  # Can SSH to private subnets
  egress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.2.0/24", "10.0.3.0/24"]
  }

  # Can download packages
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "bastion-sg"
  }
}

# Security group for database (allows SSH from bastion only)
resource "aws_security_group" "database_sg" {
  name        = "database-security-group"
  description = "Security group for database"
  vpc_id      = aws_vpc.main.id

  # Only bastion can SSH
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion_sg.id]
  }

  # Only app servers can access database
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  # Database only responds, no outbound needed
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = []
  }

  tags = {
    Name = "database-sg"
  }
}

# Launch bastion EC2 instance
resource "aws_instance" "bastion" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = "t2.micro"
  key_name              = aws_key_pair.bastion_key.key_name
  subnet_id             = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.bastion_sg.id]

  # Assign Elastic IP (stays the same even if instance restarts)
  associate_public_ip_address = true

  tags = {
    Name = "bastion-host"
  }
}

# Elastic IP for stable access
resource "aws_eip" "bastion_eip" {
  instance = aws_instance.bastion.id
  domain   = "vpc"

  tags = {
    Name = "bastion-eip"
  }
}

output "bastion_public_ip" {
  value       = aws_eip.bastion_eip.public_ip
  description = "Public IP of bastion host"
}

output "bastion_private_ip" {
  value       = aws_instance.bastion.private_ip
  description = "Private IP of bastion host"
}
```

#### Manual Setup Steps

```bash
# 1. Generate SSH key pair (on your local machine)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/bastion_key.pem
# Keep bastion_key.pem private, upload bastion_key.pem.pub to AWS

# 2. Apply Terraform to create infrastructure
terraform apply

# 3. Get bastion public IP
BASTION_IP=$(terraform output -raw bastion_public_ip)
echo "Bastion IP: $BASTION_IP"

# 4. SSH to bastion
ssh -i ~/.ssh/bastion_key.pem ec2-user@$BASTION_IP

# 5. You're now on bastion, copy database key to it
# (On your local machine, upload database key to bastion)
scp -i ~/.ssh/bastion_key.pem ~/.ssh/database_key.pem ec2-user@$BASTION_IP:~/.ssh/

# 6. SSH to bastion again and change permissions
ssh -i ~/.ssh/bastion_key.pem ec2-user@$BASTION_IP
chmod 600 ~/.ssh/database_key.pem

# 7. SSH to database from bastion
ssh -i ~/.ssh/database_key.pem ubuntu@10.0.3.30
# Now you're inside the private database server!
```

### Bastion Host Usage

#### Method 1: Two-Step SSH (Manual)

```bash
# Step 1: SSH to bastion
ssh -i ~/.ssh/bastion_key.pem ec2-user@54.123.45.67

# Step 2: From bastion prompt, SSH to database
[ec2-user@bastion ~]$ ssh -i ~/.ssh/database_key.pem ubuntu@10.0.3.30
[ubuntu@database ~]$ 

# Now you're on the database server
# Run psql to connect to PostgreSQL
psql -U postgres -h localhost
postgres=# SELECT VERSION();
```

#### Method 2: SSH Tunneling (One Command)

```bash
# Connect through bastion in one command
ssh -i ~/.ssh/bastion_key.pem \
    -J ec2-user@54.123.45.67 \
    ubuntu@10.0.3.30

# -J: Jump through bastion
# Result: Direct SSH to database, routed through bastion
```

#### Method 3: Port Forwarding (Access database locally)

```bash
# Forward database port to your local machine
ssh -i ~/.ssh/bastion_key.pem \
    -J ec2-user@54.123.45.67 \
    -L 5432:10.0.3.30:5432 \
    ubuntu@10.0.3.30 \
    sleep 1000

# Now on your local machine:
psql -h localhost -U postgres
# Connects to database through bastion!
```

---

## Real-World Scenarios

### Scenario 1: Developer Needs to Debug Database Issue

```
Developer's local machine:
$ ssh -i bastion.pem -J ec2-user@54.123.45.67 ubuntu@10.0.3.30
Last login: Fri Oct 24 10:00:00 2025 from 10.0.1.10

ubuntu@database:~$ sudo tail -f /var/log/postgresql/postgresql.log
[ERROR] connection timeout from 10.0.2.20

# Found the issue! App server at 10.0.2.20 can't reach database
# Fix: Restart app server

ubuntu@database:~$ exit

$ ssh -i bastion.pem -J ec2-user@54.123.45.67 ubuntu@10.0.2.20
ubuntu@app:~$ sudo systemctl restart myapp
ubuntu@app:~$ sudo tail -f /var/log/myapp.log
[INFO] Connected to database successfully

# Issue resolved! Data flow:
# Developer's laptop → Bastion (54.123.45.67) → Database (10.0.3.30)
# All traffic encrypted through SSH tunnel
```

### Scenario 2: Database Maintenance

```
DBA needs to:
1. Create backup
2. Run migrations
3. Check disk space

Path:
DBA's laptop → Bastion → Database

Commands:
$ ssh -i bastion.pem -J ec2-user@54.123.45.67 ubuntu@10.0.3.30

# Create backup
ubuntu@database:~$ sudo pg_dump -U postgres mydb > /tmp/backup.sql

# Run migration
ubuntu@database:~$ psql -U postgres < /tmp/migration.sql

# Check disk space
ubuntu@database:~$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       50G   35G   15G  70% /

# Everything goes through bastion
# Database never exposed to internet
```

### Scenario 3: Emergency Access Control

```
Scenario: Employee leaves company
Need to: Revoke their SSH access immediately

Option 1: Update bastion security group
- Update IP restriction from "203.0.113.45/32" to nothing
- Employee can no longer SSH to bastion
- No access to any private resources
- Takes 30 seconds

Option 2: Rotate bastion key pair
- Generate new key pair
- Update AWS key pair
- All previous keys stop working
- Takes 5 minutes

This is why bastion is powerful:
- Single point of control
- Easy to manage access
- Audit trail: all connections logged
```

---

## Security Implementation

### Defense in Depth

```
Layer 1: AWS API
├─ IAM: Who can create/modify infrastructure
└─ Must authenticate to AWS account

Layer 2: Network Layer
├─ VPC: Your isolated network
├─ Subnets: Security zones
├─ Internet Gateway: Controlled entry point
└─ NAT Gateway: Controlled exit point

Layer 3: Firewall (Security Groups)
├─ Bastion: Only from YOUR_IP
├─ Application: Only from other private resources
└─ Database: Only from application and bastion

Layer 4: SSH Authentication
├─ Public key cryptography (not passwords)
├─ Key pair: only owner has private key
└─ Bastion key + Database key: two separate keys

Layer 5: Operating System
├─ SSH daemon configuration
├─ Fail2ban: Block brute force
└─ Firewall rules on the server itself

Layer 6: Application Layer
├─ Database authentication
├─ Role-based access control
└─ Audit logging

Attacker must breach ALL layers to get data!
```

### Audit Trail / Logging

```
All access through bastion is logged:

1. Bastion SSH access
~/.ssh/authorized_keys (who connected when)
/var/log/auth.log (SSH connection attempts)

2. Bastion to database SSH
[ec2-user@bastion ~]$ history
# Shows which hosts connected, when

3. Database activity
PostgreSQL logs: all queries, connections
/var/log/postgresql/postgresql.log

4. AWS CloudTrail
- Who launched the bastion instance
- Who modified security groups
- When and from where

Compliance = Evidence that only authorized people accessed data
```

### Access Revocation

```
Immediate revocation (emergency):
1. Find IP in bastion security group
2. Remove it or change to different IP
3. User immediately locked out
4. Takes 30 seconds

Full revocation (when employee leaves):
1. Remove from IAM
2. Remove SSH key from bastion
3. Remove SSH key from all private resources
4. Change database password
5. Rotate encryption keys

User can no longer access anything!
```

---

## Terraform Best Practices

### Directory Structure

```
terraform/
├── main.tf                      # Main configuration
├── vpc.tf                       # VPC, subnets, gateways
├── security_groups.tf           # All security groups
├── bastion.tf                   # Bastion configuration
├── database.tf                  # Database resources
├── variables.tf                 # Input variables
├── outputs.tf                   # Output values
├── terraform.tfvars             # Variable values
├── terraform.tfvars.example     # Example for new users
├── .terraform.lock.hcl          # Lock file (commit to git)
├── modules/
│   ├── vpc/                     # VPC module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── bastion/                 # Bastion module
│   └── database/                # Database module
├── environments/
│   ├── dev.tfvars               # Dev environment
│   ├── staging.tfvars           # Staging environment
│   └── production.tfvars        # Production environment
└── bootstrap/                   # Initial S3 backend setup
    └── main.tf
```

### State Management Security

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

# Why this matters:
# - bucket: Where state is stored
# - encrypt: Encrypts state file at rest
# - dynamodb_table: Prevents concurrent modifications
# - key: Different key per environment

# State file contains:
# - AWS credentials
# - Database passwords
# - SSH private keys
# - Sensitive data
#
# MUST BE ENCRYPTED AND PROTECTED!
```

### Modularizing Terraform

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true

  tags = var.tags
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidr
  availability_zone = var.availability_zone

  tags = var.tags
}

# modules/vpc/variables.tf
variable "vpc_cidr" {
  type = string
}

variable "public_subnet_cidr" {
  type = string
}

variable "availability_zone" {
  type = string
}

variable "tags" {
  type = map(string)
}

# modules/vpc/outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

# main.tf (using module)
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr              = "10.0.0.0/16"
  public_subnet_cidr    = "10.0.1.0/24"
  availability_zone     = "us-east-1a"
  tags = {
    Environment = "production"
    Project     = "myapp"
  }
}

# Benefits:
# - Reusable across projects
# - Easier to maintain
# - Testable
# - Shareable with team
```

---

## Advanced Bastion Patterns

### HA Bastion (High Availability)

```
Single bastion = single point of failure
If it goes down, no access to private resources

HA solution:

┌────────────────────────────────────────────┐
│ AZ us-east-1a                              │
│ ┌──────────────────────────────────────┐   │
│ │ Bastion 1 (54.123.45.67)            │   │
│ │ + EIP (stays same if restart)       │   │
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ AZ us-east-1b                              │
│ ┌──────────────────────────────────────┐   │
│ │ Bastion 2 (54.123.45.68)            │   │
│ │ + EIP (different from bastion 1)    │   │
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘

You can SSH to either:
ssh -i bastion.pem ec2-user@54.123.45.67
ssh -i bastion.pem ec2-user@54.123.45.68

Or use DNS with failover:
bastion.example.com → resolves to active bastion
If bastion 1 dies, manually update DNS to bastion 2
```

### Bastion with Auto-scaling

```
Kubernetes uses bastion patterns for all deployments:

Every pod in VPC has a way to access:
- Other pods (through service names)
- External APIs (through NAT gateway)
- Restricted resources (through RBAC)

This is the same principle as bastion!
- Single entry point
- Multiple replicas
- Controlled access
- Audit trail
```

---

## Summary

### When to Use Each Component

| Component | Purpose | Example |
|-----------|---------|---------|
| VPC | Isolated network | 10.0.0.0/16 |
| Public Subnet | Internet-facing | Web servers |
| Private Subnet | Hidden | Databases, internal apps |
| Internet Gateway | Access to internet | HTTP/HTTPS traffic |
| NAT Gateway | Private → internet | Download packages |
| Bastion Host | SSH access to private | Admin management |
| Security Groups | Firewall rules | Port restrictions |
| Route Tables | Traffic direction | 0.0.0.0/0 → IGW |

### Key Takeaways

1. **Defense in Depth**: Multiple layers of security
2. **Least Privilege**: Only necessary permissions
3. **Single Entry Point**: Bastion controls all SSH access
4. **Audit Trail**: All actions logged
5. **Scalability**: Design for growth
6. **High Availability**: Redundancy across AZs

This is enterprise-grade infrastructure!
