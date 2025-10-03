# ============================================================================
# Output Values for Smart Contract Rewriter Infrastructure
# ============================================================================

# ============================================================================
# VPC Outputs
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.internet_gateway_id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = module.vpc.nat_gateway_ids
}

# ============================================================================
# EC2 Outputs
# ============================================================================

output "ec2_instance_ids" {
  description = "List of EC2 instance IDs"
  value       = module.ec2.instance_ids
}

output "ec2_public_ips" {
  description = "List of public IP addresses of EC2 instances"
  value       = module.ec2.public_ips
  sensitive   = false
}

output "ec2_private_ips" {
  description = "List of private IP addresses of EC2 instances"
  value       = module.ec2.private_ips
}

output "ec2_security_group_id" {
  description = "Security group ID for EC2 instances"
  value       = module.ec2.security_group_id
}

output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.ec2.load_balancer_dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.ec2.load_balancer_zone_id
}

# ============================================================================
# RDS Outputs
# ============================================================================

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = var.create_rds ? module.rds.db_endpoint : null
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = var.create_rds ? module.rds.db_port : null
}

output "rds_instance_id" {
  description = "RDS instance ID"
  value       = var.create_rds ? module.rds.db_instance_id : null
}

output "rds_instance_class" {
  description = "RDS instance class"
  value       = var.create_rds ? module.rds.db_instance_class : null
}

output "rds_security_group_id" {
  description = "Security group ID for RDS"
  value       = var.create_rds ? module.rds.security_group_id : null
}

# ============================================================================
# S3 Outputs
# ============================================================================

output "s3_bucket_id" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.app_storage.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.app_storage.arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.app_storage.bucket_domain_name
}

# ============================================================================
# General Infrastructure Outputs
# ============================================================================

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = data.aws_availability_zones.available.names
}

# ============================================================================
# Connection Information
# ============================================================================

output "database_connection_string" {
  description = "Database connection string (without password)"
  value = var.create_rds ? format(
    "postgresql://%s@%s:%s/%s",
    var.db_username,
    module.rds.db_endpoint,
    module.rds.db_port,
    var.db_name
  ) : null
  sensitive = true
}

output "application_url" {
  description = "Application URL"
  value       = var.create_load_balancer ? format("http://%s", module.ec2.load_balancer_dns_name) : null
}

# ============================================================================
# Resource ARNs (for IAM policies and monitoring)
# ============================================================================

output "resource_arns" {
  description = "ARNs of created resources"
  value = {
    s3_bucket = aws_s3_bucket.app_storage.arn
    rds_instance = var.create_rds ? module.rds.db_arn : null
    vpc = module.vpc.vpc_arn
  }
}

# ============================================================================
# Monitoring and Logging
# ============================================================================

output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value = {
    application = "/aws/ec2/${local.name_prefix}"
    database    = var.create_rds ? "/aws/rds/instance/${module.rds.db_instance_id}/postgresql" : null
  }
}

# ============================================================================
# Security Information
# ============================================================================

output "security_groups" {
  description = "Security group information"
  value = {
    ec2_sg_id = module.ec2.security_group_id
    rds_sg_id = var.create_rds ? module.rds.security_group_id : null
  }
}

# ============================================================================
# Cost Tracking Tags
# ============================================================================

output "cost_tracking_tags" {
  description = "Tags for cost tracking and management"
  value = {
    Project     = var.project_name
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }
}