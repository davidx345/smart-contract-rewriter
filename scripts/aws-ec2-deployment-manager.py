#!/usr/bin/env python3
"""
🚀 SoliVolt AWS EC2 Deployment Manager
Complete EC2 setup, deployment, and monitoring for microservices
"""

import os
import sys
import time
import json
import boto3
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import paramiko
from botocore.exceptions import ClientError

class AWSEC2DeploymentManager:
    """
    Complete AWS EC2 deployment manager for SoliVolt microservices
    """
    
    def __init__(self):
        # AWS Configuration
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # EC2 Configuration
        self.instance_type = os.getenv('EC2_INSTANCE_TYPE', 't3.micro')  # Free tier
        self.key_pair_name = os.getenv('EC2_KEY_PAIR_NAME', 'solivolt-key-pair')
        self.security_group_name = os.getenv('EC2_SECURITY_GROUP', 'solivolt-sg')
        
        # Application Configuration
        self.app_name = 'solivolt'
        self.docker_image = 'solivolt/microservices'
        
        # Initialize AWS clients
        try:
            self.ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            self.ec2_resource = boto3.resource(
                'ec2',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
        except Exception as e:
            self.log(f"❌ AWS client initialization failed: {e}", "ERROR")
            self.ec2_client = None
            self.ec2_resource = None
        
        # Deployment thresholds
        self.health_check_timeout = 300  # 5 minutes
        self.deployment_timeout = 600    # 10 minutes
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[32m",    # Green
            "WARN": "\033[33m",    # Yellow  
            "ERROR": "\033[31m",   # Red
            "DEPLOY": "\033[36m",  # Cyan
            "SUCCESS": "\033[92m", # Bright Green
            "RESET": "\033[0m"     # Reset
        }
        
        color = colors.get(level, colors["INFO"])
        print(f"{color}[{timestamp}] {message}{colors['RESET']}")
    
    def check_aws_credentials(self) -> bool:
        """Check if AWS credentials are properly configured"""
        try:
            if not self.ec2_client:
                return False
            
            # Test credentials by making a simple API call
            self.ec2_client.describe_regions()
            self.log("✅ AWS credentials verified", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"❌ AWS credentials check failed: {e}", "ERROR")
            return False
    
    def create_key_pair(self) -> bool:
        """Create EC2 key pair for SSH access"""
        try:
            self.log(f"🔑 Creating key pair: {self.key_pair_name}", "DEPLOY")
            
            # Check if key pair already exists
            try:
                self.ec2_client.describe_key_pairs(KeyNames=[self.key_pair_name])
                self.log(f"✅ Key pair {self.key_pair_name} already exists", "INFO")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != 'InvalidKeyPair.NotFound':
                    raise e
            
            # Create new key pair
            response = self.ec2_client.create_key_pair(KeyName=self.key_pair_name)
            
            # Save private key to file
            key_file_path = f"{self.key_pair_name}.pem"
            with open(key_file_path, 'w') as key_file:
                key_file.write(response['KeyMaterial'])
            
            # Set proper permissions (Unix-like systems)
            if os.name != 'nt':  # Not Windows
                os.chmod(key_file_path, 0o600)
            
            self.log(f"✅ Key pair created and saved to {key_file_path}", "SUCCESS")
            self.log(f"🔒 Keep this file secure! It's your SSH private key", "WARN")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to create key pair: {e}", "ERROR")
            return False
    
    def create_security_group(self) -> str:
        """Create security group with proper rules for SoliVolt"""
        try:
            self.log(f"🛡️ Creating security group: {self.security_group_name}", "DEPLOY")
            
            # Check if security group already exists
            try:
                response = self.ec2_client.describe_security_groups(
                    GroupNames=[self.security_group_name]
                )
                sg_id = response['SecurityGroups'][0]['GroupId']
                self.log(f"✅ Security group {self.security_group_name} already exists: {sg_id}", "INFO")
                return sg_id
            except ClientError as e:
                if e.response['Error']['Code'] != 'InvalidGroup.NotFound':
                    raise e
            
            # Create security group
            response = self.ec2_client.create_security_group(
                GroupName=self.security_group_name,
                Description='SoliVolt microservices security group'
            )
            sg_id = response['GroupId']
            
            # Add security rules
            security_rules = [
                {'port': 22, 'protocol': 'tcp', 'description': 'SSH access'},
                {'port': 80, 'protocol': 'tcp', 'description': 'HTTP'},
                {'port': 443, 'protocol': 'tcp', 'description': 'HTTPS'},
                {'port': 8000, 'protocol': 'tcp', 'description': 'API Gateway'},
                {'port': 3000, 'protocol': 'tcp', 'description': 'Frontend'},
                {'port': 9090, 'protocol': 'tcp', 'description': 'Prometheus'},
                {'port': 3001, 'protocol': 'tcp', 'description': 'Grafana'},
            ]
            
            for rule in security_rules:
                self.ec2_client.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': rule['protocol'],
                            'FromPort': rule['port'],
                            'ToPort': rule['port'],
                            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': rule['description']}]
                        }
                    ]
                )
            
            self.log(f"✅ Security group created: {sg_id}", "SUCCESS")
            return sg_id
            
        except Exception as e:
            self.log(f"❌ Failed to create security group: {e}", "ERROR")
            return ""
    
    def launch_ec2_instance(self, security_group_id: str) -> str:
        """Launch EC2 instance with Docker pre-installed"""
        try:
            self.log(f"🚀 Launching EC2 instance ({self.instance_type})", "DEPLOY")
            
            # User data script to install Docker and dependencies
            user_data_script = """#!/bin/bash
# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install Git
yum install -y git

# Install Python 3 and pip
yum install -y python3 python3-pip

# Create application directory
mkdir -p /home/ec2-user/solivolt
chown ec2-user:ec2-user /home/ec2-user/solivolt

# Install AWS CLI
pip3 install awscli

# Install other useful tools
yum install -y htop curl wget nano

echo "EC2 instance setup completed" > /home/ec2-user/setup-complete.txt
"""
            
            # Launch instance
            response = self.ec2_resource.create_instances(
                ImageId='ami-0c02fb55956c7d316',  # Amazon Linux 2 AMI (us-east-1)
                MinCount=1,
                MaxCount=1,
                InstanceType=self.instance_type,
                KeyName=self.key_pair_name,
                SecurityGroupIds=[security_group_id],
                UserData=user_data_script,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': f'{self.app_name}-server'},
                            {'Key': 'Project', 'Value': 'SoliVolt'},
                            {'Key': 'Environment', 'Value': 'production'}
                        ]
                    }
                ]
            )
            
            instance = response[0]
            instance_id = instance.id
            
            self.log(f"🎯 Instance launched: {instance_id}", "SUCCESS")
            self.log("⏳ Waiting for instance to be running...", "INFO")
            
            # Wait for instance to be running
            instance.wait_until_running()
            instance.reload()
            
            public_ip = instance.public_ip_address
            self.log(f"✅ Instance is running! Public IP: {public_ip}", "SUCCESS")
            
            # Save instance details to file
            instance_info = {
                'instance_id': instance_id,
                'public_ip': public_ip,
                'public_dns': instance.public_dns_name,
                'key_pair': self.key_pair_name,
                'security_group': security_group_id,
                'region': self.aws_region,
                'created_at': datetime.now().isoformat()
            }
            
            with open('ec2-instance-info.json', 'w') as f:
                json.dump(instance_info, f, indent=2)
            
            self.log("📄 Instance details saved to ec2-instance-info.json", "INFO")
            
            return instance_id
            
        except Exception as e:
            self.log(f"❌ Failed to launch EC2 instance: {e}", "ERROR")
            return ""
    
    def wait_for_ssh(self, public_ip: str, max_wait: int = 300) -> bool:
        """Wait for SSH to be available on the instance"""
        self.log("⏳ Waiting for SSH to be available...", "INFO")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                # Try to connect via SSH
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((public_ip, 22))
                sock.close()
                
                if result == 0:
                    self.log("✅ SSH is available!", "SUCCESS")
                    return True
                    
            except Exception:
                pass
            
            time.sleep(10)
            self.log("⏳ Still waiting for SSH...", "INFO")
        
        self.log("❌ SSH connection timeout", "ERROR")
        return False
    
    def deploy_application(self, public_ip: str) -> bool:
        """Deploy SoliVolt microservices to EC2 instance"""
        try:
            self.log("🚀 Starting application deployment", "DEPLOY")
            
            key_file = f"{self.key_pair_name}.pem"
            if not os.path.exists(key_file):
                self.log(f"❌ Private key file not found: {key_file}", "ERROR")
                return False
            
            # SSH connection details
            ssh_command_base = [
                'ssh', '-i', key_file,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                f'ec2-user@{public_ip}'
            ]
            
            # Upload docker-compose file
            scp_command = [
                'scp', '-i', key_file,
                '-o', 'StrictHostKeyChecking=no',
                'microservices/docker-compose.microservices.yml',
                f'ec2-user@{public_ip}:/home/ec2-user/docker-compose.yml'
            ]
            
            self.log("📦 Uploading docker-compose configuration", "DEPLOY")
            result = subprocess.run(scp_command, capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"❌ Failed to upload docker-compose: {result.stderr}", "ERROR")
                return False
            
            # Create deployment script
            deployment_script = """#!/bin/bash
set -e

echo "🚀 Starting SoliVolt deployment"

# Navigate to app directory
cd /home/ec2-user

# Create environment file
cat > .env << 'EOF'
GEMINI_API_KEY=your_actual_gemini_api_key_here
SECRET_KEY=super-secret-jwt-key-microservices-2024
DEBUG=false
ENVIRONMENT=production
EOF

# Pull and start services
echo "📦 Starting microservices..."
docker-compose -f docker-compose.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check if main service is responding
echo "🔍 Checking application health..."
if curl -f http://localhost:8000/health; then
    echo "✅ Application deployed successfully!"
else
    echo "❌ Application health check failed"
    exit 1
fi

echo "🎉 Deployment completed!"
"""
            
            # Upload and execute deployment script
            with open('deploy.sh', 'w') as f:
                f.write(deployment_script)
            
            # Upload deployment script
            scp_deploy_command = [
                'scp', '-i', key_file,
                '-o', 'StrictHostKeyChecking=no',
                'deploy.sh',
                f'ec2-user@{public_ip}:/home/ec2-user/deploy.sh'
            ]
            
            subprocess.run(scp_deploy_command, check=True)
            
            # Execute deployment
            ssh_deploy_command = ssh_command_base + ['chmod +x deploy.sh && ./deploy.sh']
            
            self.log("🎯 Executing deployment on EC2 instance", "DEPLOY")
            result = subprocess.run(ssh_deploy_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Application deployed successfully!", "SUCCESS")
                self.log(f"🌐 Application URL: http://{public_ip}:8000", "SUCCESS")
                self.log(f"📊 Monitoring: http://{public_ip}:3001", "SUCCESS")
                return True
            else:
                self.log(f"❌ Deployment failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Deployment error: {e}", "ERROR")
            return False
    
    def full_setup_and_deploy(self) -> bool:
        """Complete EC2 setup and deployment process"""
        self.log("🚀 Starting complete AWS EC2 setup and deployment", "DEPLOY")
        
        # Step 1: Check AWS credentials
        if not self.check_aws_credentials():
            self.log("❌ AWS credentials not configured properly", "ERROR")
            self.log("💡 Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables", "INFO")
            return False
        
        # Step 2: Create key pair
        if not self.create_key_pair():
            return False
        
        # Step 3: Create security group
        security_group_id = self.create_security_group()
        if not security_group_id:
            return False
        
        # Step 4: Launch EC2 instance
        instance_id = self.launch_ec2_instance(security_group_id)
        if not instance_id:
            return False
        
        # Get instance details
        try:
            instance = self.ec2_resource.Instance(instance_id)
            public_ip = instance.public_ip_address
            
            # Step 5: Wait for SSH
            if not self.wait_for_ssh(public_ip):
                return False
            
            # Wait a bit more for user data script to complete
            self.log("⏳ Waiting for instance initialization to complete...", "INFO")
            time.sleep(60)
            
            # Step 6: Deploy application
            if not self.deploy_application(public_ip):
                return False
            
            self.log("🎉 Complete setup and deployment successful!", "SUCCESS")
            self.log(f"🔗 Your SoliVolt application is ready at: http://{public_ip}:8000", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Setup process failed: {e}", "ERROR")
            return False

def main():
    """Main function to run the deployment"""
    print("🚀 SoliVolt AWS EC2 Deployment Manager")
    print("=====================================")
    
    manager = AWSEC2DeploymentManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            manager.full_setup_and_deploy()
        elif command == "deploy":
            # Deploy to existing instance
            if os.path.exists('ec2-instance-info.json'):
                with open('ec2-instance-info.json', 'r') as f:
                    instance_info = json.load(f)
                manager.deploy_application(instance_info['public_ip'])
            else:
                print("❌ No instance info found. Run 'setup' first.")
        elif command == "check":
            manager.check_aws_credentials()
        else:
            print("Usage: python aws-ec2-deployment-manager.py [setup|deploy|check]")
    else:
        # Interactive mode
        print("Available commands:")
        print("1. setup  - Complete EC2 setup and deployment")
        print("2. deploy - Deploy to existing instance")
        print("3. check  - Check AWS credentials")
        
        choice = input("Enter command: ").strip()
        
        if choice == "setup" or choice == "1":
            manager.full_setup_and_deploy()
        elif choice == "deploy" or choice == "2":
            if os.path.exists('ec2-instance-info.json'):
                with open('ec2-instance-info.json', 'r') as f:
                    instance_info = json.load(f)
                manager.deploy_application(instance_info['public_ip'])
            else:
                print("❌ No instance info found. Run 'setup' first.")
        elif choice == "check" or choice == "3":
            manager.check_aws_credentials()

if __name__ == "__main__":
    main()
