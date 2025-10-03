# 🏗️ Infrastructure as Code with Terraform

This directory contains the complete Infrastructure as Code (IaC) implementation for the Smart Contract Rewriter platform using Terraform.

## 📁 Directory Structure

```
terraform/
├── main.tf                    # Main Terraform configuration
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output definitions
├── versions.tf                # Provider version constraints
├── bootstrap/                 # State backend bootstrap
│   └── main.tf               # S3 + DynamoDB setup
├── modules/                   # Reusable Terraform modules
│   ├── vpc/                  # VPC networking module
│   ├── ec2/                  # EC2 compute module
│   └── rds/                  # RDS database module
└── environments/             # Environment-specific configurations
    ├── dev/
    │   └── terraform.tfvars
    └── prod/
        └── terraform.tfvars
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install Terraform
# Windows (Chocolatey)
choco install terraform

# macOS (Homebrew)
brew install terraform

# Verify installation
terraform version

# Configure AWS CLI
aws configure
```

### 2. Bootstrap Remote State (One-time setup)

```bash
# Navigate to bootstrap directory
cd terraform/bootstrap

# Initialize and apply bootstrap
terraform init
terraform plan
terraform apply

# Note the output values for backend configuration
```

### 3. Deploy Infrastructure

```powershell
# Using the deployment script (recommended)
.\scripts\deploy-infrastructure.ps1 -Environment dev -Action plan
.\scripts\deploy-infrastructure.ps1 -Environment dev -Action apply

# Or manually
cd terraform
terraform init
terraform workspace select dev
terraform plan -var-file="environments/dev/terraform.tfvars"
terraform apply -var-file="environments/dev/terraform.tfvars"
```

## 🏛️ Architecture Overview

### Network Architecture
- **VPC**: Isolated virtual private cloud
- **Public Subnets**: Internet-facing resources (Load Balancer, NAT Gateways)
- **Private Subnets**: Application servers (EC2 instances)
- **Database Subnets**: RDS instances (isolated from internet)

### Compute Architecture
- **Auto Scaling Groups**: Automatic scaling based on demand
- **Application Load Balancer**: Traffic distribution and health checks
- **EC2 Instances**: Containerized application hosting
- **Security Groups**: Network-level firewall rules

### Data Architecture
- **RDS PostgreSQL**: Managed relational database
- **S3 Buckets**: Object storage for files and backups
- **DynamoDB**: Terraform state locking

## 🔧 Module Documentation

### VPC Module (`modules/vpc/`)

Creates a complete networking setup with:
- VPC with configurable CIDR
- Public, private, and database subnets across multiple AZs
- Internet Gateway and NAT Gateways
- Route tables and security groups
- VPC Flow Logs for monitoring

**Usage:**
```hcl
module "vpc" {
  source = "./modules/vpc"
  
  project_name       = "smart-contract-rewriter"
  environment        = "dev"
  vpc_cidr          = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
  
  tags = local.common_tags
}
```

### EC2 Module (`modules/ec2/`)

Manages compute resources including:
- Auto Scaling Groups with launch templates
- Application Load Balancer
- Security groups for web and SSH access
- CloudWatch monitoring and alarms
- Instance profile with necessary IAM roles

### RDS Module (`modules/rds/`)

Handles database infrastructure:
- RDS PostgreSQL with Multi-AZ support
- Automated backups and maintenance windows
- Parameter and subnet groups
- Security groups for database access
- Enhanced monitoring and performance insights

## 🌍 Environment Management

### Development Environment
- Single instance for cost optimization
- Smaller instance types
- Reduced backup retention
- Simplified monitoring

### Production Environment
- Multi-instance with auto-scaling
- Production-grade instance types
- Extended backup retention
- Comprehensive monitoring

### Workspace Strategy
```bash
# List workspaces
terraform workspace list

# Create new workspace
terraform workspace new staging

# Switch workspace
terraform workspace select prod
```

## 🔒 Security Features

### Infrastructure Security
- **VPC Isolation**: Private subnets for application tiers
- **Security Groups**: Least privilege network access
- **IAM Roles**: Granular permissions for resources
- **Encryption**: At-rest and in-transit encryption
- **Network ACLs**: Additional network security layer

### State Security
- **Remote State**: Encrypted S3 backend
- **State Locking**: DynamoDB prevents concurrent modifications
- **Versioning**: S3 versioning for state history
- **Access Control**: IAM policies for state access

### Security Scanning
```bash
# Install security scanners
go install github.com/aquasecurity/tfsec/cmd/tfsec@latest
pip install checkov

# Run security scans
tfsec .
checkov -d . --framework terraform

# Or use the deployment script
.\scripts\deploy-infrastructure.ps1 -Environment dev -Action security-scan
```

## 💰 Cost Optimization

### Cost Estimation
```bash
# Install Infracost
curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh

# Generate cost estimate
infracost breakdown --path .

# Or use the deployment script
.\scripts\deploy-infrastructure.ps1 -Environment dev -Action cost-estimate
```

### Cost-Saving Features
- **Spot Instances**: Optional for non-critical workloads
- **Auto Scaling**: Scale down during low usage
- **Reserved Instances**: For predictable workloads
- **Resource Tagging**: Cost allocation and tracking

### Resource Tagging Strategy
```hcl
common_tags = {
  Project     = "smart-contract-rewriter"
  Environment = var.environment
  Owner       = "DevOps-Team"
  ManagedBy   = "Terraform"
  CostCenter  = "Engineering"
  CreatedAt   = timestamp()
}
```

## 📊 Monitoring and Alerting

### CloudWatch Integration
- **VPC Flow Logs**: Network traffic monitoring
- **EC2 Metrics**: CPU, memory, disk utilization
- **RDS Metrics**: Database performance monitoring
- **Application Logs**: Centralized log aggregation

### Custom Metrics
```hcl
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${local.name_prefix}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ec2 cpu utilization"
}
```

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
name: Terraform
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      
      - name: Terraform Format
        run: terraform fmt -check
        
      - name: Terraform Init
        run: terraform init
        
      - name: Terraform Validate
        run: terraform validate
        
      - name: Terraform Plan
        run: terraform plan -var-file="environments/dev/terraform.tfvars"
```

### GitOps Workflow
1. **Feature Branch**: Create infrastructure changes
2. **Pull Request**: Automated validation and planning
3. **Code Review**: Manual review of infrastructure changes
4. **Merge**: Automatic deployment to development
5. **Release**: Manual promotion to production

## 🛠️ Troubleshooting

### Common Issues

**State Lock Error:**
```bash
# Force unlock (use carefully!)
terraform force-unlock <LOCK_ID>
```

**Backend Configuration Error:**
```bash
# Reconfigure backend
terraform init -reconfigure
```

**Resource Drift:**
```bash
# Detect drift
terraform plan -detailed-exitcode

# Import existing resources
terraform import aws_instance.example i-1234567890abcdef0
```

### Debugging Commands
```bash
# Enable detailed logging
export TF_LOG=DEBUG

# Validate configuration
terraform validate

# Show current state
terraform show

# List resources
terraform state list

# Show specific resource
terraform state show aws_instance.example
```

## 📚 Advanced Topics

### Custom Modules
Create reusable modules for common patterns:
```hcl
# modules/monitoring/
# modules/security/
# modules/networking/
```

### Workspace Automation
```bash
# Automated workspace management
for env in dev staging prod; do
  terraform workspace select $env
  terraform plan -var-file="environments/$env/terraform.tfvars"
done
```

### State Management
```bash
# Backup state
aws s3 cp s3://your-state-bucket/terraform.tfstate ./backup/

# State manipulation
terraform state mv aws_instance.old aws_instance.new
terraform state rm aws_instance.unused
```

## 🎯 Phase 5 Achievement Checklist

- [x] **Terraform Modules**: Reusable VPC, EC2, and RDS modules
- [x] **Remote State**: S3 backend with DynamoDB locking
- [x] **Infrastructure Versioning**: Environment-specific configurations
- [x] **Cost Estimation**: Infracost integration for cost tracking
- [x] **Security Scanning**: tfsec and Checkov integration
- [x] **Deployment Automation**: PowerShell deployment script
- [x] **Documentation**: Comprehensive setup and usage guides
- [x] **Best Practices**: Tagging, naming conventions, security

## 📖 Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [Infrastructure as Code Patterns](https://docs.aws.amazon.com/whitepapers/latest/introduction-devops-aws/infrastructure-as-code.html)

---

**🎉 Congratulations!** You've successfully implemented Infrastructure as Code with Terraform, completing Phase 5 of your DevOps roadmap. Your infrastructure is now:
- **Reproducible**: Consistent deployments across environments
- **Scalable**: Auto-scaling and load balancing
- **Secure**: Encrypted, monitored, and access-controlled
- **Cost-Optimized**: Tagged and monitored for cost efficiency
- **Production-Ready**: Ready for enterprise deployment