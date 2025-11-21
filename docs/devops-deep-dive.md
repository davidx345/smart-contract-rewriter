# DevOps & Cloud Engineering: Deep Dive (Phase 1-6)

A comprehensive guide to understanding enterprise-grade cloud architecture, from fundamentals to Kubernetes orchestration.

---

## Table of Contents

1. [Phase 1: Core Foundations](#phase-1-core-foundations)
2. [Phase 2: Containers & Cloud Compute](#phase-2-containers--cloud-compute)
3. [Phase 3: CI/CD Pipelines](#phase-3-cicd-pipelines)
4. [Phase 4: Cloud Storage, Databases & Networking](#phase-4-cloud-storage-databases--networking)
5. [Phase 5: Infrastructure as Code](#phase-5-infrastructure-as-code)
6. [Phase 6: Kubernetes & Orchestration](#phase-6-kubernetes--orchestration)
 
---

# Phase 1: Core Foundations

## The Building Blocks of Cloud Infrastructure

Before you can build cloud infrastructure, you need to understand the fundamentals: Linux, networking, version control, and cloud provider basics.

### Linux Administration Deep Dive

#### Understanding Processes and System Management

```bash
# A process is a running instance of a program with its own memory space and resources
# Every process has a Process ID (PID)

# View all running processes
ps aux

# Output format:
# USER: Process owner
# PID: Process ID (unique identifier)
# %CPU: CPU usage percentage
# %MEM: Memory usage percentage
# VSZ: Virtual memory size (KB)
# RSS: Resident set size (actual physical memory used, KB)
# STAT: Process state (R=running, S=sleeping, Z=zombie, T=stopped)

# Example:
# root       1  0.0  0.2  19356  2352 ?  Ss  10:00  0:01 /sbin/init
# The 'init' process (PID 1) is the parent of all processes

# Kill a process by PID
kill -9 1234  # -9 = SIGKILL (forceful termination)
kill -15 1234 # -15 = SIGTERM (graceful termination)

# The difference:
# - SIGTERM (15): Asks process to shut down gracefully, allows cleanup
# - SIGKILL (9): Immediately terminates, no cleanup (last resort)

# Monitor processes in real-time
top
# Interactive: q=quit, k=kill, f=fields
```

**Why This Matters in Cloud:**
When deploying microservices, you need to understand process management. Docker containers run a single process. When you scale to Kubernetes, you're orchestrating thousands of processes across multiple machines. Understanding PIDs, states, and signals helps you debug container failures.

#### Users, Permissions, and Security

```bash
# Everything in Linux is owned by a user and has permissions
# Permissions: read (4), write (2), execute (1)

# Check file permissions
ls -la /etc/passwd
# -rw-r--r-- 1 root root 2847 Oct 24 10:00 /etc/passwd
#  ^^^^^^^^^^   ^^^^        
#  permissions owner

# Permission breakdown for "drwxr-xr-x":
# d: directory (vs - for file)
# rwx (owner): user can read, write, execute
# r-x (group): group can read and execute, NOT write
# r-x (others): others can read and execute, NOT write

# This is critical in cloud security:
# - Private key files should be 600 (rw-------)
# - Only the owner can read it
chmod 600 ~/.ssh/id_rsa

# Create a new user (often done when setting up CI/CD agents)
useradd -m -s /bin/bash deployuser
# -m: create home directory
# -s: specify shell

# Add user to sudoers (grants root privileges)
usermod -aG sudo deployuser
# Now this user can run commands with sudo

# This is how you secure: restricted users, minimal permissions
```

**Why This Matters in Cloud:**
In Kubernetes, you run containers as non-root users for security. If a container is compromised, the attacker can't gain full system access. In your terraform code, you restrict IAM user permissions to specific AWS actions. Same principle.

#### System Services (systemd)

```bash
# systemd is the init system that manages services
# A service is a process that runs in the background

# Start, stop, restart services
systemctl start docker      # Start Docker daemon
systemctl stop docker       # Stop Docker daemon
systemctl restart docker    # Restart Docker daemon
systemctl status docker     # Check status

# Enable service to start automatically on boot
systemctl enable docker     # Docker starts when system boots
systemctl disable docker    # Docker won't start on boot

# View service logs
journalctl -u docker -f
# -u: unit (service name)
# -f: follow (tail -f style)

# Example service file: /etc/systemd/system/my-app.service
# [Unit]
# Description=My Application
# After=network.target
# 
# [Service]
# Type=simple
# User=appuser
# ExecStart=/usr/bin/python3 /app/main.py
# Restart=always
# 
# [Install]
# WantedBy=multi-user.target

# Why this matters: In your VMs, you might run a service that:
# - Polls GitHub for new deployments
# - Restarts Docker containers
# - Monitors system health
# You need to ensure it survives reboots and restarts automatically
```

**Real-world example from Phase 6:**
When your Kubernetes node crashes and restarts, systemd ensures kubelet (the Kubernetes agent) restarts automatically and rejoins the cluster.

### Networking Fundamentals

#### IP Addresses and CIDR Notation

```
An IP address is like a postal address for your computer on a network.
Format: XXX.XXX.XXX.XXX (4 octets, each 0-255)

Example: 192.168.1.100
- 192.168.1 = network
- 100 = host

CIDR (Classless Inter-Domain Routing) notation:
192.168.0.0/24 means:
- 192.168.0.x (where x = 0-255)
- /24 = first 24 bits are the network portion
- This gives 256 addresses (192.168.0.0 to 192.168.0.255)

Breaking it down:
- /32: 1 address (single host)
- /24: 256 addresses
- /16: 65,536 addresses
- /8: 16 million addresses

In the context of AWS VPCs:
- Your VPC might be 10.0.0.0/16 (65,536 addresses)
- Public subnets: 10.0.1.0/24 (256 addresses for web servers)
- Private subnets: 10.0.2.0/24 (256 addresses for databases)
```

#### DNS: The Phone Book of the Internet

```bash
# DNS translates domain names to IP addresses
# Without DNS, you'd need to memorize IP addresses

nslookup google.com
# Name Server Lookup
# Returns: 142.250.185.46

# This means when you visit google.com, your browser:
# 1. Queries DNS: "What IP is google.com?"
# 2. Gets response: "142.250.185.46"
# 3. Connects to 142.250.185.46

# In your cloud infrastructure:
# - Service discovery: Backend containers need to find database
# - Kubernetes uses DNS: database-service.default.svc.cluster.local
# - Your app does: curl http://database-service:5432
# - Kubernetes DNS resolves this to the actual pod IP
```

### Port and Firewall Concepts

```
A port is like a "door" to a service on your computer.

Well-known ports:
- 22: SSH (secure shell)
- 80: HTTP (web)
- 443: HTTPS (secure web)
- 3306: MySQL
- 5432: PostgreSQL
- 6379: Redis
- 8000: Common API port

A firewall is like a security guard that says:
"Only traffic on these ports from these IPs is allowed"

Example rule:
- Source: 192.168.1.0/24 (only machines on this network)
- Destination Port: 22 (SSH)
- Action: ALLOW

This means: "Only computers on the 192.168.1.x network can SSH to this server"

In AWS, this is a Security Group.
```

### Git: The Source Control Foundation

```bash
# Git is version control - tracks changes to files over time

# Core concepts:
# Repository: Folder with all project files and history
# Commit: A snapshot of your code at a point in time
# Branch: A parallel version of your code
# Remote: A copy of your repo on a server (GitHub)

# Basic workflow:
git clone https://github.com/user/repo  # Download repo
cd repo
git checkout -b feature/new-api         # Create new branch
# ... make changes ...
git add .                               # Stage changes
git commit -m "Add new API endpoint"    # Create commit
git push origin feature/new-api         # Push to GitHub
# Then create a Pull Request for review

# Why this matters for DevOps:
# - Infrastructure as Code (Terraform) is stored in Git
# - CI/CD pipelines trigger on git push
# - You can rollback to previous versions
# - Multiple people can work without conflicts
```

### AWS Account Setup and IAM

```
IAM = Identity and Access Management
Think of it as a key management system for AWS.

Root Account (Like the master key):
- Unlimited access
- Can access all AWS services
- Should never be used for daily work
- Should have MFA (multi-factor authentication)

IAM Users (Like individual keys):
- Limited access to specific services
- Each person gets their own account
- Can grant access to:
  - EC2 (compute)
  - S3 (storage)
  - RDS (databases)
  - etc.

Example IAM Policy (JSON):
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}

This means: Allow this user to GET and LIST objects in my-bucket only

Principle of Least Privilege:
- Give users the minimum permissions needed
- If a user only needs to read S3, don't give EC2 access
- If compromised, damage is limited
```

---

# Phase 2: Containers & Cloud Compute

## Containerization and Cloud VMs

### Docker: What and Why?

```
PROBLEM BEFORE DOCKER:
- Developer: "It works on my machine!"
- DevOps Engineer: "It doesn't work in production"
- Reason: Different OS, different libraries, different Python version

SOLUTION: Docker
- Package your application with all its dependencies
- Same container runs everywhere: local machine, CI/CD, AWS, etc.
- Lightweight: shares host OS kernel, unlike VMs
```

#### How Docker Works

```bash
# Docker creates an "image" - a blueprint
# Then creates "containers" - running instances

# Dockerfile: Instructions to build an image
FROM python:3.11              # Start with Python 3.11 base image
WORKDIR /app                  # Set working directory
COPY requirements.txt .       # Copy dependency file
RUN pip install -r requirements.txt  # Install dependencies
COPY . .                      # Copy application code
EXPOSE 8000                   # This container listens on port 8000
CMD ["python", "main.py"]     # When container starts, run this

# Build the image
docker build -t my-app:1.0 .
# -t: tag (name and version)
# .: build context (where Dockerfile is)

# Run a container from the image
docker run -p 8000:8000 my-app:1.0
# -p: port mapping
#     8000 (host) -> 8000 (container)
# You can now access http://localhost:8000

# Layers: Each line in Dockerfile creates a layer
# FROM python:3.11 ← Layer 1 (Python base image)
# WORKDIR /app ← Layer 2 (create directory)
# COPY requirements.txt . ← Layer 3
# RUN pip install... ← Layer 4
# COPY . . ← Layer 5
# EXPOSE 8000 ← Layer 6
# CMD ["python", "main.py"] ← Layer 7

# Docker caches layers: if you only change Layer 5 (code), 
# layers 1-4 are reused (fast rebuild)
```

#### Multi-stage Docker Builds

```dockerfile
# Stage 1: Builder
FROM python:3.11 as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .
RUN python -m py_compile *.py  # Check for syntax errors

# Stage 2: Runtime (minimal)
FROM python:3.11-slim          # Smaller base image
WORKDIR /app
COPY --from=builder /app .     # Copy from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["python", "main.py"]

# Result: Final image only has runtime dependencies, not build tools
# Final image ~300MB instead of ~800MB
# Security: Build tools not present, smaller attack surface
```

**Why this matters:**
In Phase 6, you deploy these images to Kubernetes. Smaller images = faster startup, faster scaling.

### Docker Compose: Multi-container Orchestration

```yaml
# docker-compose.yml: Define multiple containers and how they talk

version: '3.8'

services:
  # Service 1: Web Application
  backend:
    build: ./backend          # Build from Dockerfile in ./backend
    ports:
      - "8000:8000"           # Map port 8000
    environment:              # Environment variables inside container
      DATABASE_URL: "postgresql://postgres:password@db:5432/myapp"
      DEBUG: "false"
    depends_on:
      db:                      # This service depends on 'db' service
        condition: service_healthy  # Don't start until db is healthy
    networks:
      - app-network           # Connect to this network
    healthcheck:              # Docker checks if service is healthy
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s           # Check every 30 seconds
      timeout: 10s            # Wait max 10 seconds for response
      retries: 3              # If 3 checks fail, mark unhealthy

  # Service 2: Database
  db:
    image: postgres:15        # Use pre-built image
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persistent storage
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  # Service 3: Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network

networks:
  app-network:                # Docker creates a network for service discovery
    driver: bridge            # Services can reach each other by name

volumes:
  postgres_data:              # Named volume for database persistence
```

**Key insight:**
When you run `docker-compose up`, Docker creates:
1. A network called `app-network`
2. Services can reach each other by name: `backend` connects to `db` as `postgresql://db:5432`
3. This is similar to how Kubernetes services work (Phase 6)

### AWS EC2: Cloud Virtual Machines

```
EC2 = Elastic Compute Cloud
It's basically a computer you rent from AWS

Instance types (different sizes):
- t2.micro: 1 CPU, 1 GB RAM ($0.0116/hour) - Free tier
- t2.small: 1 CPU, 2 GB RAM
- m5.large: 2 CPU, 8 GB RAM
- c5.xlarge: 4 CPU, 8 GB RAM
- etc.

The "t" in t2 means "burstable" - can handle traffic spikes

When you launch an EC2 instance:
1. Choose an AMI (Amazon Machine Image)
   - AMI is a pre-built OS image
   - Ubuntu, Amazon Linux, Windows, etc.
2. Choose instance type (t2.micro, m5.large, etc.)
3. Configure networking (VPC, subnet, security groups)
4. Add storage (EBS volumes - elastic block storage)
5. Tag for organization
6. Assign security group (firewall rules)
7. Assign key pair (SSH access)
```

#### Security Groups: Cloud Firewalls

```
A Security Group defines what traffic is allowed in/out

Inbound rules (traffic coming TO your instance):
- Port 22 (SSH) from 0.0.0.0/0 (anywhere)
  → Anyone can SSH to this instance
- Port 80 (HTTP) from 0.0.0.0/0
  → Anyone can access HTTP
- Port 5432 (PostgreSQL) from 10.0.0.0/16
  → Only instances in this network can access database

Outbound rules (traffic going FROM your instance):
- Default: Allow all (instance can reach anywhere)
- You can restrict to only allow access to specific services

Example Security Group for web server:
┌─────────────┐
│ Security    │
│ Group: Web  │
├─────────────┤
│ Inbound:    │
│ - 80 (HTTP) │
│ - 443 (HTTPS)
│ - 22 (SSH)  │
│ from 10.0.x │
│             │
│ Outbound:   │
│ - 443 (HTTPS)  (to reach APIs)
│ - 3306 (MySQL) (to reach DB)
│ - 53 (DNS)     (to resolve domains)
└─────────────┘
```

#### SSH: Secure Shell Access

```bash
# SSH is how you login to remote servers
# Uses public-key cryptography (safer than passwords)

# Generate a key pair (do this on your local machine)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/my-key.pem
# -t rsa: use RSA algorithm
# -b 4096: 4096 bits (more secure than 2048)
# Result: my-key.pem (private key) and my-key.pem.pub (public key)

# NEVER share private key!
# Public key goes on server, private key stays on your machine

# When you launch EC2 instance:
# 1. AWS puts your public key on the instance
# 2. You download the private key

# Connect to instance:
ssh -i my-key.pem ec2-user@54.123.45.67
# -i: identity file (private key)
# ec2-user: default user on Amazon Linux
# 54.123.45.67: public IP of instance

# Behind the scenes:
# 1. Your computer sends: "I'm user ec2-user"
# 2. Server checks: "Do I have the public key for this user?"
# 3. Server sends: "Here's a challenge, sign it with your private key"
# 4. Your SSH client signs with private key
# 5. Server verifies signature with public key
# 6. Connection established

# The key pair solves the problem:
# - No password to intercept
# - Cryptographically secure
# - Can be rotated (revoke old, issue new)
```

---

# Phase 4: Cloud Storage, Databases & Networking (VPC Deep Dive)

## VPC: Virtual Private Cloud - Your Own Network in AWS

This is where things get complex, but also where the power lies. A VPC is essentially your own isolated network within AWS.

### VPC Basics

```
Before VPC, all AWS customers were on the same network - dangerous!

VPC solves this: Each customer gets their own isolated network

You decide:
- IP range (CIDR block)
- How to segment it (subnets)
- How traffic flows (route tables)
- What connects to the internet
- What stays private

Example:
┌─────────────────────────────────────────────────────────┐
│  AWS Region (e.g., us-east-1)                           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Your VPC: 10.0.0.0/16                           │  │
│  │                                                   │  │
│  │  ┌──────────────────┐    ┌──────────────────┐   │  │
│  │  │ Public Subnet 1  │    │ Private Subnet   │   │  │
│  │  │ 10.0.1.0/24      │    │ 10.0.2.0/24      │   │  │
│  │  │                  │    │                  │   │  │
│  │  │ ┌──────────────┐ │    │ ┌──────────────┐ │   │  │
│  │  │ │   Web Server │ │    │ │   Database   │ │   │  │
│  │  │ │ 10.0.1.10    │ │    │ │ 10.0.2.20    │ │   │  │
│  │  │ └──────────────┘ │    │ └──────────────┘ │   │  │
│  │  │                  │    │                  │   │  │
│  │  │ Has internet     │    │ No internet      │   │  │
│  │  │ access           │    │ access (private) │   │  │
│  │  └──────────────────┘    └──────────────────┘   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Subnets: Dividing Your VPC

A subnet is a division of your VPC - a smaller network within it.

```
Why split into subnets?

1. AVAILABILITY ZONES (AZ): AWS regions have multiple AZs
   - Each AZ is a separate data center
   - If one fails, you have backups in another
   - Subnets must be in ONE AZ

2. SECURITY: Different security levels
   - Public: Web servers (need internet access)
   - Private: Databases (no internet access)
   - Protected: Bastion hosts (jump servers)

3. ORGANIZATION: Logical grouping
   - Frontend tier
   - Application tier
   - Database tier


Multi-AZ Setup (Highly Available):
┌────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16                                       │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  AZ: us-east-1a  │  │  AZ: us-east-1b  │            │
│  │                  │  │                  │            │
│  │ Public Subnet    │  │ Public Subnet    │            │
│  │ 10.0.1.0/24      │  │ 10.0.3.0/24      │            │
│  │                  │  │                  │            │
│  │ Web Server 1     │  │ Web Server 2     │            │
│  │ 10.0.1.10        │  │ 10.0.3.10        │            │
│  │                  │  │                  │            │
│  ├──────────────────┤  ├──────────────────┤            │
│  │ Private Subnet   │  │ Private Subnet   │            │
│  │ 10.0.2.0/24      │  │ 10.0.4.0/24      │            │
│  │                  │  │                  │            │
│  │ Database 1       │  │ Database 2       │            │
│  │ (Primary)        │  │ (Replica/Backup) │            │
│  └──────────────────┘  └──────────────────┘            │
└────────────────────────────────────────────────────────┘

Benefits:
- If us-east-1a datacenter has issues, us-east-1b continues
- Load balancer distributes traffic between both
- High availability = 99.99% uptime
```

#### Subnet IPs: What Gets Used?

```
When you create a subnet 10.0.1.0/24, AWS reserves some IPs:

10.0.1.0     - Network address (reserved)
10.0.1.1     - VPC router (reserved)
10.0.1.2     - DNS server (reserved)
10.0.1.3     - Reserved for future use
10.0.1.4     - 10.0.1.254 = available for instances
10.0.1.255   - Broadcast address (reserved)

So in a /24 subnet (256 IPs total):
- 5 reserved
- 251 available for your instances

This is why you usually use:
- /24 for small subnets: 251 usable IPs
- /22 for medium: 1019 usable IPs
- /20 for large: 4091 usable IPs
```

### Internet Gateway: Your Connection to the Internet

```
Internet Gateway = Door to the internet

Without it: Your VPC is completely isolated
With it: Can reach internet and internet can reach you

┌──────────────────────────────────┐
│  Public Subnet                   │
│  ┌────────────────────────────┐  │
│  │ Web Server                 │  │
│  │ 10.0.1.10                 │  │
│  └────────────────────────────┘  │
│            ↓                      │
│  ┌────────────────────────────┐  │
│  │ Internet Gateway           │  │
│  │ Converts private IP to     │  │
│  │ public IP for routing      │  │
│  └────────────────────────────┘  │
│            ↓                      │
│  AWS Network → Internet           │
│            ↓                      │
│  54.123.45.67 (Public IP)        │
│            ↓                      │
│  Browser on internet reaches it  │
└──────────────────────────────────┘

How it works:
1. You set up Internet Gateway and attach to VPC
2. Create public subnet
3. Add route: 0.0.0.0/0 → Internet Gateway
   (This means: any traffic not destined for VPC, send to IGW)
4. Assign public IP to instance
5. Now instance can reach internet

Rule: Traffic inside VPC → stays in VPC
      Traffic outside VPC → goes through IGW
```

### NAT Gateway: How Private Subnets Reach Internet

Private subnets have NO direct internet access. But sometimes they need it:
- Download security patches
- Connect to external APIs
- Pull Docker images

Solution: NAT Gateway

```
NAT = Network Address Translation

┌──────────────────────────────────┐
│  Private Subnet                  │
│  ┌────────────────────────────┐  │
│  │ Database Server            │  │
│  │ 10.0.2.20                 │  │
│  │ (wants to download patch)  │  │
│  └────────────────────────────┘  │
│            ↓                      │
│  ┌────────────────────────────┐  │
│  │ NAT Gateway                │  │
│  │ (in public subnet)         │  │
│  │ Private IP: 10.0.1.50      │  │
│  │ Public IP: 54.200.1.1      │  │
│  └────────────────────────────┘  │
│            ↓                      │
│  Internet Gateway                │
│            ↓                      │
│  Internet: 54.200.1.1 → patch    │
│            ↓                      │
│  Response: 54.200.1.1 ← patch    │
│            ↓                      │
│  NAT translates back to database │
│            ↓                      │
│  Database: 10.0.2.20 ← patch     │
└──────────────────────────────────┘

How NAT works:
1. Private instance sends: "Get me this file from internet"
2. NAT intercepts and changes:
   - Source: 10.0.2.20 → 54.200.1.1
3. Internet sends response to 54.200.1.1
4. NAT translates back:
   - Destination: 54.200.1.1 → 10.0.2.20
5. Private instance receives response

Why not let private subnet connect directly?
- Security: Private instances not exposed to internet
- If a hacker gets in, they can't directly access it
- All outbound traffic goes through ONE gateway (easier to monitor)
```

### Bastion Host (Jump Server): The Security Guardian

This is critical for managing private resources.

```
THE PROBLEM:
┌──────────────────┐
│  Private Subnet  │
│  Database Server │
│  10.0.2.20       │
│  NO internet IP  │
└──────────────────┘

You're at home, want to SSH to database to run queries.
But database has no public IP!
How do you reach it?

SOLUTION: Bastion Host (Jump Server)

┌────────────────────────────────────────────────────┐
│  Public Subnet                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Bastion Host (Jump Server)                  │  │
│  │  - Has public IP: 54.123.45.67               │  │
│  │  - Has SSH enabled                           │  │
│  │  - Only has SSH access (minimal)             │  │
│  │  - Cannot reach internet (only SSH)          │  │
│  │  10.0.1.5                                    │  │
│  └──────────────────────────────────────────────┘  │
│           ↑ (SSH from internet)                    │
│                                                    │
│  ┌────────────────────────────────────────────────┐ │
│  │  Private Subnet                                │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │  Database Server                         │ │ │
│  │  │  10.0.2.20                               │ │ │
│  │  │  - NO public IP                          │ │ │
│  │  │  - Hidden from internet                  │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  │           ↑ (SSH from bastion)                │ │
│  └────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘

Architecture:
Your Laptop (home)
    ↓ SSH port 22
Bastion Host (54.123.45.67)
    ↓ SSH port 22 (internal network)
Database (10.0.2.20)

STEP 1: SSH to bastion
ssh -i bastion-key.pem ec2-user@54.123.45.67

STEP 2: From bastion, SSH to database
ssh -i database-key.pem ubuntu@10.0.2.20

OR: SSH tunneling (do it in one command)
ssh -i bastion-key.pem -J ec2-user@54.123.45.67 ubuntu@10.0.2.20
# -J: jump host
```

**Why Bastion Host is Secure:**

```
Attack Surface Reduction:
- Only ONE machine publicly accessible
- Database is completely hidden
- Bastion acts as a choke point
- All access goes through one place (easy to audit/log)

Example Security Group for Bastion:
┌───────────────────────────────────────────┐
│ Bastion Security Group                    │
├───────────────────────────────────────────┤
│ Inbound:                                  │
│ - SSH (22) from YOUR_IP only              │
│   (not from 0.0.0.0/0, from your IP)      │
│ - NO other ports                          │
│                                           │
│ Outbound:                                 │
│ - SSH (22) to 10.0.2.0/24 (DB subnet)    │
│ - SSH (22) to 10.0.3.0/24 (app subnet)   │
│ - NO internet access (no HTTP/HTTPS)     │
│                                           │
│ Result: Bastion can ONLY:                │
│ - Receive SSH from you                    │
│ - Send SSH to internal servers            │
│ - Cannot reach internet                   │
│ - Cannot be used for other purposes       │
└───────────────────────────────────────────┘

Bastion Host is like:
- Fort entrance (heavily guarded)
- Only soldiers can enter/exit
- Once inside the fort, you move to other areas
- Attacker must breach the entrance first
```

### Route Tables: Traffic Controller

```
Route table decides where traffic goes.

"If you're trying to reach 10.0.1.x, go directly"
"If you're trying to reach 8.8.8.8 (Google DNS), go through Internet Gateway"

Public Subnet Route Table:
Destination        Target
10.0.0.0/16       Local (stay in VPC)
0.0.0.0/0         Internet Gateway

This means:
- Anything for 10.0.0.0/16 → stays local
- Everything else (0.0.0.0/0) → goes to internet

Private Subnet Route Table:
Destination        Target
10.0.0.0/16       Local (stay in VPC)
0.0.0.0/0         NAT Gateway

This means:
- Anything for 10.0.0.0/16 → stays local
- Everything else → goes through NAT

Database Subnet Route Table (most restricted):
Destination        Target
10.0.0.0/16       Local (stay in VPC)

This means:
- Anything for 10.0.0.0/16 → stays local
- Everything else → BLOCKED (nowhere to go)
```

### Network ACLs: Layer 2 Firewall

You have TWO firewalls:
1. Security Groups (attached to instances)
2. Network ACLs (attached to subnets)

```
Network ACLs are stateless (unlike Security Groups which are stateful)

Stateless = You must explicitly allow BOTH inbound AND outbound
Stateful = If you allow inbound, outbound response is automatic

Example: Download a file
Stateful Security Group:
- Inbound: Allow SSH (22) - automatically allows responses
- When you SSH, responses come back through port 22
- You don't need separate outbound rule

Stateless NACL:
- Inbound: Allow SSH (22)
- Outbound: Must also allow responses on port 22
- Or else responses are blocked!

Most common approach:
- Use Security Groups for fine-grained control
- NACLs as additional layer (usually allow-all then restrict with SGs)
```

### Security Group vs NACL

```
┌─────────────────────────────────────────┐
│           Security Group                │
│  (Instance level)                       │
│                                         │
│  Stateful                               │
│  Allow/Deny                             │
│  Can reference other SGs                │
│  All rules evaluated                    │
│                                         │
│    ↓                                    │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Network ACL                      │  │
│  │  (Subnet level)                   │  │
│  │                                   │  │
│  │  Stateless                        │  │
│  │  Allow/Deny                       │  │
│  │  Cannot reference SGs             │  │
│  │  Rules evaluated in order (first  │  │
│  │  match wins)                      │  │
│  │                                   │  │
│  │    ↓                              │  │
│  │                                   │  │
│  │  Instance receives traffic        │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

Default Security Group:
- Allow all traffic between instances in same SG
- Deny all inbound from outside

Default NACL:
- Allow all traffic

This is why Security Groups are primary defense.
```

---

# Phase 5: Infrastructure as Code (Terraform)

## Infrastructure as Code Principle

```
Before IaC: Manual Clicking
- Click AWS console
- Click buttons to create VPC, subnets, security groups
- Click to create databases
- Hard to reproduce
- Prone to mistakes
- Can't version control

After IaC (Terraform):
- Write code that describes infrastructure
- Version control it (Git)
- Reproduce exactly
- Peer review before deployment
- Rollback if needed
```

### Terraform Basics

```hcl
# main.tf: Infrastructure as code

# Define AWS provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Store state in S3 (not local file)
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

# Create VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "main-vpc"
    Environment = var.environment
  }
}

# Create public subnet in AZ us-east-1a
resource "aws_subnet" "public_1a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true  # Automatically assigns public IP

  tags = {
    Name = "public-subnet-1a"
  }
}

# Create private subnet in AZ us-east-1a
resource "aws_subnet" "private_1a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "private-subnet-1a"
  }
}

# Create Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}

# Create NAT Gateway for private subnet internet access
resource "aws_eip" "nat" {
  domain = "vpc"
  
  tags = {
    Name = "nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_1a.id  # NAT goes in public subnet

  tags = {
    Name = "nat-gateway"
  }

  depends_on = [aws_internet_gateway.main]
}

# Public route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-rt"
  }
}

# Associate public subnet with public route table
resource "aws_route_table_association" "public_1a" {
  subnet_id      = aws_subnet.public_1a.id
  route_table_id = aws_route_table.public.id
}

# Private route table (through NAT)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "private-rt"
  }
}

# Associate private subnet with private route table
resource "aws_route_table_association" "private_1a" {
  subnet_id      = aws_subnet.private_1a.id
  route_table_id = aws_route_table.private.id
}

# Create bastion security group
resource "aws_security_group" "bastion" {
  name        = "bastion-sg"
  description = "Security group for bastion host"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.your_ip]  # Only your IP can SSH
  }

  egress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    cidr_blocks     = ["10.0.2.0/24"]  # Can SSH to private subnet
  }

  tags = {
    Name = "bastion-sg"
  }
}

# Create bastion EC2 instance
resource "aws_instance" "bastion" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t2.micro"
  
  # Put it in public subnet
  subnet_id = aws_subnet.public_1a.id
  
  # Assign security group
  vpc_security_group_ids = [aws_security_group.bastion.id]
  
  # Use your SSH key
  key_name = aws_key_pair.deployer.key_name

  tags = {
    Name = "bastion-host"
  }
}

# Output the bastion public IP
output "bastion_public_ip" {
  value = aws_instance.bastion.public_ip
}
```

**Terraform Workflow:**

```bash
# 1. Write code (as shown above)

# 2. Initialize Terraform
terraform init
# Downloads AWS provider, sets up .terraform directory

# 3. Plan (see what will be created)
terraform plan
# Output shows: + (will create), - (will destroy), ~ (will modify)

# 4. Apply (create infrastructure)
terraform apply
# Reviews plan, asks for confirmation, creates resources

# 5. Destroy (delete everything)
terraform destroy
# Deletes all resources created by Terraform
```

**Why This Matters:**

```
Before Terraform:
- Click, click, click through AWS console
- Hard to reproduce in another account
- Manual errors
- Can't code review infrastructure

With Terraform:
- Infrastructure is version controlled
- Peer review: "Does this security group look right?"
- Reproducible: Same code → same infrastructure
- Testable: Plan before you apply
- Documented: The code IS the documentation
```

---

# Phase 6: Kubernetes & Orchestration

## Kubernetes Concepts

Kubernetes is an orchestration platform for containers. It solves:

```
PROBLEM: Running thousands of containers across many machines
- Which container runs on which machine?
- What if a container crashes?
- How do you scale up/down?
- How do containers find each other?
- How do you update without downtime?

KUBERNETES SOLUTION: Automated container orchestration
```

### Kubernetes Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Kubernetes Cluster                                      │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Control Plane (Master)                             │ │
│  │  ┌──────────────┐                                   │ │
│  │  │ API Server   │ (Central command center)          │ │
│  │  └──────────────┘                                   │ │
│  │  ┌──────────────┐                                   │ │
│  │  │ etcd         │ (Stores all data)                 │ │
│  │  └──────────────┘                                   │ │
│  │  ┌──────────────┐                                   │ │
│  │  │ Scheduler    │ (Decides where pods go)           │ │
│  │  └──────────────┘                                   │ │
│  │  ┌──────────────┐                                   │ │
│  │  │ Controller   │ (Maintains desired state)         │ │
│  │  │ Manager      │                                   │ │
│  │  └──────────────┘                                   │ │
│  └─────────────────────────────────────────────────────┘ │
│                        ↓                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Worker Nodes (Machines running containers)         │ │
│  │                                                       │ │
│  │  Node 1: us-east-1a          Node 2: us-east-1b     │ │
│  │  ┌──────────────────────┐    ┌──────────────────┐   │ │
│  │  │ kubelet              │    │ kubelet          │   │ │
│  │  │ (K8s agent)          │    │ (K8s agent)      │   │ │
│  │  │                      │    │                  │   │ │
│  │  │ ┌────────────────┐   │    │ ┌──────────────┐ │   │ │
│  │  │ │ Pod: backend   │   │    │ │ Pod: backend │ │   │ │
│  │  │ │ (container)    │   │    │ │ (container)  │ │   │ │
│  │  │ └────────────────┘   │    │ └──────────────┘ │   │ │
│  │  │ ┌────────────────┐   │    │ ┌──────────────┐ │   │ │
│  │  │ │ Pod: database  │   │    │ │ Pod: cache   │ │   │ │
│  │  │ │ (container)    │   │    │ │ (container)  │ │   │ │
│  │  │ └────────────────┘   │    │ └──────────────┘ │   │ │
│  │  └──────────────────────┘    └──────────────────┘   │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘

Control Plane: Brain of the cluster
- Makes decisions (where to run pods, scaling, updates)
- Is highly available (usually 3 replicas)

Worker Nodes: Where work happens
- Run containers in pods
- Report health to control plane
- Execute commands from control plane
```

### Pods: The Smallest Kubernetes Unit

```
A Pod is a wrapper around a container (usually 1:1)

Why not just use containers?
- Kubernetes orchestrates Pods, not containers
- A pod can have multiple containers (rare, but possible)
- Pod shares network namespace: containers share IP

Example pod with one container:
apiVersion: v1
kind: Pod
metadata:
  name: myapp
  labels:
    app: backend
spec:
  containers:
  - name: app
    image: myapp:1.0
    ports:
    - containerPort: 8000

Why not just run containers directly?
- Containers are ephemeral (can be deleted, replaced)
- Pods are managed: if pod dies, K8s restarts it
- Pods have unique IP addresses
- Pods can be part of higher-level abstractions (Deployments)
```

### Deployments: Managing Pods at Scale

```
Deployment = "Run 3 instances of this application"

Instead of managing individual pods, you describe desired state:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3  # Run 3 copies
  selector:
    matchLabels:
      app: backend
  template:  # Template for pods
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: myapp:1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 200m        # Minimum CPU needed
            memory: 256Mi    # Minimum memory
          limits:
            cpu: 500m        # Maximum CPU allowed
            memory: 512Mi    # Maximum memory

What Kubernetes does:
1. See "desired state: 3 replicas"
2. Create 3 pods
3. Distribute across worker nodes
4. If pod crashes, automatically restart
5. If node dies, reschedule pod on another node

Rolling updates (no downtime):
1. Current state: 3 old pods running
2. New version deployed
3. Start 1 new pod (now 3 old + 1 new = 4)
4. Stop 1 old pod (now 3 old + 1 new = 3)
5. Start another new pod (now 2 old + 2 new = 3)
6. Stop another old pod (now 2 old + 2 new = 3)
7. Continue until all updated
8. End state: 3 new pods (zero downtime!)
```

### Services: Network Abstraction

```
Problem: Pod IPs are ephemeral (change when pods restart)
Solution: Service provides stable endpoint

When you have 3 backend pods:
Pod 1: 10.1.1.10
Pod 2: 10.1.2.10
Pod 3: 10.1.3.10

Frontend has to know all 3 IPs? Bad!
What if pod dies and gets recreated with new IP?

Service solution:
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 80        # Service port
    targetPort: 8000 # Container port
  type: ClusterIP   # Internal only (not exposed to internet)

Result:
- Service gets stable IP: 10.2.1.5
- Frontend connects to: backend-service:80
- Kubernetes DNS resolves to: 10.2.1.5
- Service load-balances across all backend pods

Frontend thinks it's talking to ONE server,
but it's actually load-balanced across 3!

Different Service Types:
- ClusterIP: Internal only (default)
- NodePort: Exposed on each node's IP + port
- LoadBalancer: External load balancer (AWS ALB)
- ExternalName: Maps to external DNS
```

### StatefulSets: For Databases

```
Deployment = Stateless (pods are interchangeable)
StatefulSet = Stateful (pods have persistent identity)

Why StatefulSet for databases?

Deployment:
Pod1 (deleted/recreated) → Pod2
Pod2 is completely new, no data

Database needs:
- Persistent storage
- Stable network identity
- Ordered startup (master before replicas)

StatefulSet:
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres-headless
  replicas: 1
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi

StatefulSet provides:
- Stable pod names: postgres-0, postgres-1
- Persistent storage: data survives pod restart
- Ordered startup: postgres-0 before postgres-1
- Headless service for direct pod access
```

### Horizontal Pod Autoscaling (HPA)

```
HPA = Automatically scale pods based on metrics

Example: Traffic spike at 2 PM

Normal: 2 pods
Metrics: CPU > 70%
Action: Scale to 5 pods to handle load

When traffic drops:
Metrics: CPU < 50%
Action: Scale back to 2 pods (save costs)

Configuration:
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60

This means:
- Keep 2-10 replicas
- If CPU > 70% or Memory > 80%, scale up by 50% every 60s
- If both drop below thresholds, scale down by 10% after 5 min
- Prevents thrashing (rapid up/down)
```

### Ingress: External Access

```
How do external users reach your services?

Without Ingress:
- Service type LoadBalancer
- Each service gets its own AWS ALB
- Expensive and wasteful

With Ingress:
- One AWS ALB handles all traffic
- Routes based on hostname/path
- Cheaper and more efficient

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: main-ingress
spec:
  ingressClassName: aws-load-balancer
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 80
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000

Traffic flow:
api.example.com → DNS → 52.123.45.67 (AWS ALB)
                                ↓
                    Ingress controller
                    (Kubernetes component)
                                ↓
                    backend-service (port 80)
                                ↓
                    backend pods

This is Phase 6 in action!
```

### RBAC: Role-Based Access Control

```
RBAC = Who can do what in Kubernetes

Problem: Multiple teams in one cluster
- Platform team: manage cluster
- Backend team: deploy backend
- Database team: manage databases
- Finance: read-only access

Solution: RBAC

Define Role (what can be done):
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-developer
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["pods", "logs"]
  verbs: ["get", "list", "watch"]

This role can:
- Manage deployments (update/patch)
- View pods and logs
- Cannot delete deployments or access secrets

Bind Role to User (RoleBinding):
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-dev-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: backend-developer
subjects:
- kind: User
  name: alice@example.com
  apiGroup: rbac.authorization.k8s.io

Result: Alice can manage backend deployments, cannot delete them

ClusterRole: Cluster-wide permissions
Role: Namespace-specific permissions

Example: Admin can create/delete pods in all namespaces
Example: Developer can only update deployments in their namespace
```

### Network Policies: Kubernetes Firewalls

```
Like Security Groups in VPC, but for Kubernetes

Problem: All pods can talk to each other by default
Solution: Network policies restrict traffic

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress

This denies ALL inbound traffic to all pods.

Then add specific allows:
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

This means:
- Deny all traffic (first policy)
- But allow frontend pods to reach backend on port 8000
- Backend cannot talk to frontend (traffic is one-way)
- Database is completely isolated

Network flow:
Frontend (allowed) → Backend
Frontend (allowed) → Database (BLOCKED)
Backend → Frontend (BLOCKED)
Backend → Database (check DB network policy)
```

### Monitoring in Kubernetes

```
Three pillars of observability:

1. METRICS (numbers over time)
   - Request count per second
   - Error rate
   - Response time
   - CPU usage
   - Memory usage

2. LOGS (what happened)
   - Application errors
   - Deployment events
   - API requests

3. TRACES (request journey)
   - Request enters system
   - Goes to backend service
   - Backend queries database
   - Response back to frontend
   - Track the entire journey

Kubernetes monitoring stack:
┌────────────────┐
│ Prometheus     │ (Collects metrics)
│                │
│ Scrapes /metrics endpoint every 15s
│ Stores in time-series database
└────────────────┘
        ↓
┌────────────────┐
│ Grafana        │ (Visualizes metrics)
│                │
│ Creates dashboards
│ Shows graphs and alerts
└────────────────┘
        ↓
┌────────────────┐
│ Alertmanager   │ (Triggers alerts)
│                │
│ If metric exceeds threshold
│ Send Slack message, email, etc
└────────────────┘

Application exposes metrics:
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1234
http_requests_total{method="POST",status="201"} 567
http_requests_total{method="GET",status="404"} 89

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 100
http_request_duration_seconds_bucket{le="0.5"} 280
http_request_duration_seconds_bucket{le="1"} 430
http_request_duration_seconds_bucket{le="+Inf"} 435
http_request_duration_seconds_sum 1234.5
http_request_duration_seconds_count 435
```

---

## Summary: Your DevOps Journey

You now understand:

### Phase 1: Foundations
- Linux processes and permissions
- Networking (IPs, DNS, ports, firewalls)
- Git version control
- AWS account setup

### Phase 2: Containerization
- Docker images and containers
- Docker Compose for multi-service setup
- EC2 instances
- Security groups

### Phase 3: CI/CD
- Automated testing
- Building Docker images
- Deploying to EC2
- Rollback strategies

### Phase 4: Cloud Networking (Deep Dive)
- VPC architecture (your private network)
- Public/private subnets (divided security zones)
- Internet Gateway (connection to world)
- NAT Gateway (private subnet internet access)
- **Bastion Host** (jump server for SSH)
- Route tables (traffic direction)
- Network ACLs and Security Groups

### Phase 5: Infrastructure as Code
- Terraform (code describes infrastructure)
- Reproducible, version-controlled infrastructure
- Multi-environment setup

### Phase 6: Kubernetes
- Container orchestration at scale
- Auto-scaling based on metrics
- Rolling updates (zero downtime)
- Service discovery
- RBAC (who can do what)
- Network policies (isolation)
- Monitoring (Prometheus, Grafana)

This is enterprise-grade infrastructure!
