#!/usr/bin/env python3
"""
AWS EC2 Quick Setup Script for Microservices
Automates the creation and deployment of microservices to AWS EC2
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

class AWSQuickSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "scripts"
        
    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        print("🔍 Checking prerequisites...")
        
        required_tools = [
            ("aws", "AWS CLI"),
            ("python", "Python 3"),
            ("git", "Git")
        ]
        
        for tool, name in required_tools:
            if not self.command_exists(tool):
                print(f"❌ {name} is not installed. Please install it first.")
                return False
        
        print("✅ All prerequisites are installed")
        return True
    
    def command_exists(self, command):
        """Check if a command exists"""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def install_dependencies(self):
        """Install required Python packages"""
        print("📦 Installing AWS dependencies...")
        
        requirements_file = self.scripts_dir / "aws-requirements.txt"
        if not requirements_file.exists():
            print("❌ aws-requirements.txt not found")
            return False
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-r", str(requirements_file)
            ], check=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    
    def check_aws_credentials(self):
        """Check if AWS credentials are configured"""
        print("🔑 Checking AWS credentials...")
        
        try:
            result = subprocess.run([
                "aws", "sts", "get-caller-identity"
            ], capture_output=True, text=True, check=True)
            
            identity = json.loads(result.stdout)
            print(f"✅ AWS credentials configured for: {identity.get('Arn', 'Unknown')}")
            return True
        except subprocess.CalledProcessError:
            print("❌ AWS credentials not configured")
            print("Please run: aws configure")
            return False
    
    def create_instance(self, instance_type="t3.micro"):
        """Create EC2 instance using the deployment manager"""
        print(f"🏗️ Creating EC2 instance ({instance_type})...")
        
        deployment_script = self.scripts_dir / "aws-ec2-deployment-manager.py"
        if not deployment_script.exists():
            print("❌ AWS deployment manager not found")
            return False
        
        try:
            subprocess.run([
                sys.executable, str(deployment_script),
                "--create-instance",
                "--instance-type", instance_type,
                "--auto-approve"
            ], check=True)
            print("✅ EC2 instance created successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to create EC2 instance")
            return False
    
    def deploy_microservices(self, strategy="unified"):
        """Deploy microservices to EC2"""
        print(f"🚀 Deploying microservices (strategy: {strategy})...")
        
        deployment_script = self.scripts_dir / "aws-ec2-deployment-manager.py"
        
        try:
            subprocess.run([
                sys.executable, str(deployment_script),
                "--deploy",
                "--deployment-strategy", strategy,
                "--auto-approve"
            ], check=True)
            print("✅ Microservices deployed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to deploy microservices")
            return False
    
    def display_github_secrets(self, instance_info):
        """Display GitHub secrets that need to be configured"""
        print("\n🔐 GitHub Secrets Configuration")
        print("=" * 50)
        print("Add these secrets to your GitHub repository:")
        print()
        
        secrets = {
            "AWS_ACCESS_KEY_ID": "your_aws_access_key",
            "AWS_SECRET_ACCESS_KEY": "your_aws_secret_key", 
            "AWS_REGION": "us-east-1",
            "EC2_HOST": instance_info.get("public_ip", "your_ec2_public_ip"),
            "EC2_PRIVATE_KEY": "content_of_your_private_key_file",
            "GEMINI_API_KEY": "your_gemini_api_key",
            "SECRET_KEY": "your_jwt_secret_key",
            "DATABASE_URL": "postgresql://postgres:postgres123@localhost:5432/smart_contract_db"
        }
        
        for key, value in secrets.items():
            print(f"{key}={value}")
        
        print("\n📝 Instructions:")
        print("1. Go to your GitHub repository")
        print("2. Settings > Secrets and variables > Actions")
        print("3. Add each secret above")
        print("4. For EC2_PRIVATE_KEY, paste the entire .pem file content")
    
    def run_health_checks(self, public_ip):
        """Run basic health checks"""
        print("🔍 Running health checks...")
        
        endpoints = [
            f"http://{public_ip}:8000/health",
            f"http://{public_ip}:8001/health"
        ]
        
        for endpoint in endpoints:
            try:
                import requests
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {endpoint} - OK")
                else:
                    print(f"⚠️ {endpoint} - Status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} - Error: {e}")
    
    def run_full_setup(self):
        """Run the complete setup process"""
        print("🚀 Starting AWS EC2 Microservices Setup")
        print("=" * 50)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Check AWS credentials
        if not self.check_aws_credentials():
            return False
        
        # Create instance
        if not self.create_instance():
            return False
        
        # Wait a bit for instance to be ready
        print("⏳ Waiting for instance to be ready...")
        time.sleep(30)
        
        # Deploy microservices
        if not self.deploy_microservices():
            return False
        
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Configure GitHub secrets (see output above)")
        print("2. Push to main branch to trigger CI/CD")
        print("3. Monitor deployment in GitHub Actions")
        
        return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AWS EC2 Quick Setup for Microservices"
    )
    parser.add_argument(
        "--instance-type", 
        default="t3.micro",
        help="EC2 instance type (default: t3.micro)"
    )
    parser.add_argument(
        "--strategy",
        default="unified", 
        help="Deployment strategy (default: unified)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check prerequisites"
    )
    
    args = parser.parse_args()
    
    setup = AWSQuickSetup()
    
    if args.check_only:
        setup.check_prerequisites()
        setup.check_aws_credentials()
        return
    
    success = setup.run_full_setup()
    
    if success:
        print("\n✅ AWS EC2 setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
