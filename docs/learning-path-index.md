# Complete DevOps Learning Path: Phase 1-6

A master index for all comprehensive guides covering your journey from DevOps foundations to Kubernetes orchestration.

---

## 📚 Documentation Overview

This collection contains deep-dive guides for understanding enterprise cloud infrastructure across 6 phases.

### Quick Navigation

| Phase | Topic | Document |
|-------|-------|----------|
| **1-2** | Foundations & Containers | [devops-deep-dive.md](devops-deep-dive.md) |
| **4** | VPC & Bastion (Practical) | [vpc-bastion-practical-guide.md](vpc-bastion-practical-guide.md) |
| **1-6** | Troubleshooting & Real Scenarios | [troubleshooting-scenarios.md](troubleshooting-scenarios.md) |
| **Architecture** | System Design | [architecture.md](architecture.md) |
| **Security** | Enterprise Security | [security.md](security.md) |

---

## 🚀 What You'll Learn

### Phase 1: Core Foundations
Learn the building blocks of cloud infrastructure.

**Topics covered:**
- Linux administration (processes, users, permissions, systemd)
- Networking fundamentals (IP addresses, CIDR, DNS, ports, firewalls)
- Git version control and workflows
- AWS account setup and IAM fundamentals

**Key files:**
- [devops-deep-dive.md - Phase 1 Section](devops-deep-dive.md#phase-1-core-foundations)

**When you're done:**
- Understand how processes work and how to manage them
- Know what a VPC actually is before you use it
- Comfortable with Linux command line
- Can explain CIDR notation and IP addressing

---

### Phase 2: Containers & Cloud Compute
Containerize your applications and deploy to cloud VMs.

**Topics covered:**
- Docker fundamentals (images, containers, layers)
- Multi-stage Docker builds for efficiency
- Docker Compose for multi-container orchestration
- EC2 instances and security groups
- SSH key management

**Key files:**
- [devops-deep-dive.md - Phase 2 Section](devops-deep-dive.md#phase-2-containers--cloud-compute)
- [troubleshooting-scenarios.md - Phase 1-2 Issues](troubleshooting-scenarios.md#phase-1-2-container--linux-issues)

**Practical examples:**
- Multi-stage Dockerfile for optimization
- Docker Compose with health checks
- Security group configuration
- SSH troubleshooting

**When you're done:**
- Can build efficient Docker images
- Understand container orchestration basics
- Comfortable deploying to EC2
- Know how to debug SSH connection issues

---

### Phase 3: CI/CD Pipelines
Automate testing and deployment.

**Topics covered:**
- GitHub Actions workflows
- Automated testing in pipeline
- Security scanning (SAST, containers)
- Rolling deployments with zero downtime
- Rollback strategies

**Key files:**
- [devops-deep-dive.md - Phase 3 Section](devops-deep-dive.md#phase-3-cicd-pipelines)

**When you're done:**
- Understand CI/CD principles
- Can write GitHub Actions workflows
- Know how to implement security scanning
- Understand deployment strategies

---

### Phase 4: Cloud Storage, Databases & Networking
Deep dive into VPC architecture and bastion hosts.

**Topics covered (CRITICAL for interviews):**
- **VPC (Virtual Private Cloud)**: Your isolated network
  - Why you need it
  - How it works
  - IP allocation
  
- **Subnets**: Dividing your VPC
  - Public subnets (internet-facing)
  - Private subnets (hidden)
  - Multi-AZ for high availability
  
- **Internet Gateway**: Connection to the world
  - How traffic routes to internet
  - Public IP assignment
  
- **NAT Gateway**: Private subnet internet access
  - How private instances reach internet
  - Why it's needed
  
- **Bastion Host (Jump Server)**: THE CRITICAL PIECE
  - Why you need it
  - Security benefits
  - SSH access patterns
  - Port forwarding
  
- **Route Tables**: Traffic direction
  - How packets get routed
  - Different routes for different subnets
  
- **Security Groups & NACLs**: Firewalls
  - Stateful vs stateless
  - Defense in depth

**Key files:**
- [devops-deep-dive.md - Phase 4 Section](devops-deep-dive.md#phase-4-cloud-storage-databases--networking-vpc-deep-dive) - **ESSENTIAL**
- [vpc-bastion-practical-guide.md](vpc-bastion-practical-guide.md) - **HANDS-ON**
- [troubleshooting-scenarios.md - Phase 4 Issues](troubleshooting-scenarios.md#phase-4-vpc--networking-problems)

**Practical exercises:**
- Design 3-tier VPC (public/app/database subnets)
- Set up bastion host
- SSH tunneling exercises
- Troubleshoot connectivity issues

**When you're done:**
- Can draw VPC architecture from memory
- Understand bastion host security model
- Know the difference between NAT and IGW
- Can troubleshoot network connectivity
- Can explain to senior engineer confidently

---

### Phase 5: Infrastructure as Code
Version control your infrastructure.

**Topics covered:**
- Terraform fundamentals
- Provider configuration
- Resource creation
- Module creation and reuse
- State management (S3 + DynamoDB)
- Multi-environment setup
- Security best practices

**Key files:**
- [devops-deep-dive.md - Phase 5 Section](devops-deep-dive.md#phase-5-infrastructure-as-code-terraform)
- [troubleshooting-scenarios.md - Phase 5 Issues](troubleshooting-scenarios.md#phase-5-terraform-disasters)

**Practical examples:**
- Complete Terraform VPC setup
- Bastion host via Terraform
- State management security
- Module organization

**When you're done:**
- Can write production Terraform code
- Understand state management
- Know how to organize modules
- Can troubleshoot Terraform issues

---

### Phase 6: Kubernetes & Orchestration
Container orchestration at enterprise scale.

**Topics covered:**
- Kubernetes architecture (control plane, worker nodes)
- Pods: The smallest unit
- Deployments: Managing pods at scale
- Services: Network abstraction
- StatefulSets: For databases
- Horizontal Pod Autoscaling
- Ingress: External access
- RBAC: Access control
- Network Policies: Kubernetes firewalls
- Monitoring (Prometheus, Grafana)
- Health checks and probes
- Rolling updates and rollbacks

**Key files:**
- [devops-deep-dive.md - Phase 6 Section](devops-deep-dive.md#phase-6-kubernetes--orchestration)
- [troubleshooting-scenarios.md - Phase 6 Issues](troubleshooting-scenarios.md#phase-6-kubernetes-failures)
- [architecture.md](architecture.md) - Visual K8s architecture

**When you're done:**
- Understand Kubernetes fundamentals
- Can troubleshoot pod failures
- Know how to scale applications
- Understand network policies
- Can explain K8s architecture

---

## 🎯 Interview Preparation

### Questions You Should Be Able to Answer

#### VPC & Networking (Phase 4)
1. **"Draw a 3-tier VPC architecture"**
   - See: [vpc-bastion-practical-guide.md - Complete VPC Architecture](vpc-bastion-practical-guide.md#complete-vpc-architecture-example)
   - Answer: Public, App, Database subnets with IGW, NAT, route tables

2. **"Why use a bastion host?"**
   - See: [vpc-bastion-practical-guide.md - Why You Need Bastion](vpc-bastion-practical-guide.md#why-you-need-a-bastion-host)
   - Answer: Single entry point, audit trail, security control

3. **"How does a private subnet reach the internet?"**
   - See: [devops-deep-dive.md - NAT Gateway](devops-deep-dive.md#nat-gateway-how-private-subnets-reach-internet)
   - Answer: Through NAT gateway in public subnet

4. **"What's the difference between Security Groups and NACLs?"**
   - See: [devops-deep-dive.md - Security Group vs NACL](devops-deep-dive.md#security-group-vs-nacl)
   - Answer: Stateful vs stateless, instance vs subnet level

5. **"How do you SSH to a private database server?"**
   - See: [vpc-bastion-practical-guide.md - Bastion Usage](vpc-bastion-practical-guide.md#bastion-host-usage)
   - Answer: Through bastion using SSH jump or tunneling

#### Kubernetes (Phase 6)
6. **"What's the difference between Deployment and StatefulSet?"**
   - See: [devops-deep-dive.md - Deployments vs StatefulSets](devops-deep-dive.md#statefulsets-for-databases)
   - Answer: Deployments are stateless, StatefulSets are stateful with persistent identity

7. **"How does a Service load balance across pods?"**
   - See: [devops-deep-dive.md - Services](devops-deep-dive.md#services-network-abstraction)
   - Answer: Service gets stable IP, routes to all matching pods

8. **"How does HPA work?"**
   - See: [devops-deep-dive.md - HPA](devops-deep-dive.md#horizontal-pod-autoscaling-hpa)
   - Answer: Watches metrics, scales pods up/down based on thresholds

#### Troubleshooting (All Phases)
9. **"A pod is in CrashLoopBackOff. How do you debug?"**
   - See: [troubleshooting-scenarios.md - Pod Won't Start](troubleshooting-scenarios.md#scenario-7-pod-wont-start---crashloopbackoff)
   - Answer: Check logs, describe pod, check resource limits

10. **"Can't SSH to EC2. What do you check?"**
    - See: [troubleshooting-scenarios.md - Can't SSH](troubleshooting-scenarios.md#scenario-1-cant-ssh-to-ec2-instance)
    - Answer: Public IP, security group, SSH key permissions

---

## 📖 Learning Strategy

### Week 1-2: Foundation
1. Read [devops-deep-dive.md - Phase 1](devops-deep-dive.md#phase-1-core-foundations)
2. Practice Linux commands
3. Understand networking basics

### Week 2-3: Containers
1. Read [devops-deep-dive.md - Phase 2](devops-deep-dive.md#phase-2-containers--cloud-compute)
2. Build your first Dockerfile
3. Try Docker Compose

### Week 3-4: VPC & Networking (CRITICAL!)
1. **Read all of** [vpc-bastion-practical-guide.md](vpc-bastion-practical-guide.md)
2. Draw VPC architecture on paper
3. Understand bastion host concept thoroughly
4. Work through scenarios in [troubleshooting-scenarios.md - Phase 4](troubleshooting-scenarios.md#phase-4-vpc--networking-problems)

### Week 4-5: Terraform
1. Read [devops-deep-dive.md - Phase 5](devops-deep-dive.md#phase-5-infrastructure-as-code-terraform)
2. Write VPC code in Terraform
3. Work through Terraform issues in [troubleshooting-scenarios.md - Phase 5](troubleshooting-scenarios.md#phase-5-terraform-disasters)

### Week 5-6: Kubernetes
1. Read [devops-deep-dive.md - Phase 6](devops-deep-dive.md#phase-6-kubernetes--orchestration)
2. Deploy to Kubernetes cluster
3. Debug pod failures using [troubleshooting-scenarios.md - Phase 6](troubleshooting-scenarios.md#phase-6-kubernetes-failures)

### Week 6: Integration
1. Review all troubleshooting scenarios
2. Practice explaining each concept
3. Draw architecture diagrams
4. Prepare for interviews

---

## 💡 Key Concepts to Master

### VPC Architecture
```
┌─────────────────────────────────────────┐
│ VPC: 10.0.0.0/16                       │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Public Subnet (internet-facing) │   │
│ │ ├─ IGW (to internet)            │   │
│ │ └─ Bastion host                 │   │
│ └──────────────┬────────────────────┘   │
│                │                        │
│ ┌──────────────▼────────────────────┐   │
│ │ Private Subnet (hidden)           │   │
│ │ ├─ NAT Gateway (for internet)    │   │
│ │ └─ Backend apps                   │   │
│ └──────────────┬────────────────────┘   │
│                │                        │
│ ┌──────────────▼────────────────────┐   │
│ │ Private DB Subnet                 │   │
│ │ └─ Database (no internet)         │   │
│ └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Bastion Host Security Model
```
You → Bastion → Private Resources

Security:
- Bastion = single entry point
- Restricted IP (only you can SSH)
- Can reach internal servers
- Audit trail of all connections
- No direct internet access to private resources
```

### Kubernetes Architecture
```
Control Plane: Brains (API, etcd, Scheduler)
                    ↓
Worker Nodes: Muscles (Run containers)
                    ↓
Services: Networking (Load balance pods)
                    ↓
Ingress: External Access (AWS ALB)
```

---

## 🔗 Additional Resources

### Your Project Examples
- [Smart Contract Rewriter Architecture](architecture.md)
- [Security Implementation](security.md)
- [Setup Guide](setup-guide.md)

### Useful Tools and Commands
See [troubleshooting-scenarios.md - Common Tools](troubleshooting-scenarios.md#common-tools-and-commands)

---

## ✅ Checkpoint: Can You Explain?

By the end of Phase 6, you should be able to explain:

1. ✅ How a VPC isolates your infrastructure
2. ✅ Why bastion hosts are essential for security
3. ✅ The difference between public and private subnets
4. ✅ How NAT gateways enable internet access for private subnets
5. ✅ What CIDR notation means (10.0.0.0/24)
6. ✅ How security groups and NACLs work together
7. ✅ The Kubernetes architecture (control plane, nodes)
8. ✅ How Deployments, Services, and Ingress work together
9. ✅ How HPA automatically scales applications
10. ✅ How to troubleshoot each layer of the stack

If you can explain all of these, you're ready for interviews!

---

## 🎓 Next Steps

After Phase 6:
- **Phase 7**: Serverless & Cloud-Native Services
- **Phase 8**: Advanced Monitoring & Security
- **Phase 9**: Governance & Cost Optimization
- **Phase 10**: Multi-Cloud Architecture
- **Phase 11**: Production-Ready HA Architecture

You're building world-class DevOps skills!

---

**Last Updated**: October 24, 2025
**Level**: Comprehensive Deep Dive (Phase 1-6)
**Status**: Ready for Enterprise Interviews ✅
