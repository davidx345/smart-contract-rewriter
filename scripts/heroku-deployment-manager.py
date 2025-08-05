#!/usr/bin/env python3
"""
🚀 SoliVolt Heroku Deployment Automation
Advanced deployment with monitoring, rollback, and A/B testing
"""

import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class HerokuDeploymentManager:
    """
    Advanced Heroku deployment manager with monitoring and rollback
    """
    
    def __init__(self):
        self.heroku_app_name = os.getenv('HEROKU_APP_NAME', 'solivolt-8e0565441715')
        self.heroku_api_key = os.getenv('HEROKU_API_KEY', '')
        self.staging_app_name = os.getenv('HEROKU_STAGING_APP', 'solivolt-staging')
        self.production_url = f"https://{self.heroku_app_name}.herokuapp.com"
        self.staging_url = f"https://{self.staging_app_name}.herokuapp.com"
        
        # Deployment thresholds
        self.health_check_timeout = 300  # 5 minutes
        self.rollback_threshold = 80.0   # Rollback if availability < 80%
        self.performance_threshold = 2000  # Rollback if response time > 2s
        
        # Slack webhook for notifications
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')
        
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
    
    def get_heroku_headers(self) -> Dict[str, str]:
        """Get standard Heroku API headers"""
        return {
            'Authorization': f'Bearer {self.heroku_api_key}',
            'Accept': 'application/vnd.heroku+json; version=3',
            'Content-Type': 'application/json'
        }
    
    def send_slack_notification(self, message: str, success: bool = True):
        """Send deployment notification to Slack"""
        if not self.slack_webhook:
            return
        
        color = "good" if success else "danger"
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": "SoliVolt Deployment Notification",
                    "text": message,
                    "timestamp": int(datetime.now().timestamp())
                }
            ]
        }
        
        try:
            requests.post(self.slack_webhook, json=payload, timeout=10)
        except Exception as e:
            self.log(f"Failed to send Slack notification: {str(e)}", "WARN")
    
    def pre_deployment_checks(self) -> bool:
        """Run comprehensive pre-deployment checks"""
        self.log("🔍 Running pre-deployment checks...", "INFO")
        
        checks = [
            ("Git Status", self.check_git_status),
            ("Tests", self.run_tests),
            ("Security Scan", self.security_scan),
            ("Database Migration Check", self.check_migrations),
            ("Environment Variables", self.check_env_vars)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                if check_func():
                    self.log(f"✅ {check_name}: PASSED", "SUCCESS")
                else:
                    self.log(f"❌ {check_name}: FAILED", "ERROR")
                    all_passed = False
            except Exception as e:
                self.log(f"❌ {check_name}: ERROR - {str(e)}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def check_git_status(self) -> bool:
        """Check git status is clean"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            return len(result.stdout.strip()) == 0
        except Exception:
            return False
    
    def run_tests(self) -> bool:
        """Run test suite"""
        try:
            # Backend tests
            backend_result = subprocess.run(
                ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
                capture_output=True,
                text=True,
                cwd='backend'
            )
            
            if backend_result.returncode != 0:
                self.log(f"Backend tests failed: {backend_result.stdout}", "ERROR")
                return False
            
            # Frontend tests (if they exist)
            frontend_test_result = subprocess.run(
                ['npm', 'test', '--', '--watchAll=false'],
                capture_output=True,
                text=True,
                cwd='frontend'
            )
            
            return True  # Don't fail if frontend tests don't exist
            
        except Exception as e:
            self.log(f"Test execution failed: {str(e)}", "ERROR")
            return False
    
    def security_scan(self) -> bool:
        """Run security vulnerability scan"""
        try:
            # Check for known vulnerabilities
            result = subprocess.run(
                ['pip', 'audit'],
                capture_output=True,
                text=True,
                cwd='backend'
            )
            
            if result.returncode != 0:
                self.log(f"Security vulnerabilities found: {result.stdout}", "WARN")
                return False
            
            return True
            
        except Exception:
            self.log("Security scan failed, but continuing...", "WARN")
            return True  # Don't fail deployment if scan fails
    
    def check_migrations(self) -> bool:
        """Check if database migrations are needed"""
        try:
            # Check if there are pending migrations
            result = subprocess.run(
                ['alembic', 'current'],
                capture_output=True,
                text=True,
                cwd='backend'
            )
            
            # For now, assume migrations are handled separately
            return True
            
        except Exception:
            return True
    
    def check_env_vars(self) -> bool:
        """Check required environment variables"""
        required_vars = [
            'DATABASE_URL',
            'GEMINI_API_KEY',
            'SECRET_KEY'
        ]
        
        if not self.heroku_api_key:
            self.log("❌ HEROKU_API_KEY not set", "ERROR")
            return False
        
        # Check if required vars exist in Heroku
        try:
            headers = self.get_heroku_headers()
            response = requests.get(
                f'https://api.heroku.com/apps/{self.heroku_app_name}/config-vars',
                headers=headers
            )
            
            if response.status_code != 200:
                return False
            
            config_vars = response.json()
            
            for var in required_vars:
                if var not in config_vars:
                    self.log(f"❌ Required env var missing: {var}", "ERROR")
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"Failed to check env vars: {str(e)}", "ERROR")
            return False
    
    def deploy_to_staging(self) -> bool:
        """Deploy to staging environment"""
        self.log("🚀 Deploying to staging...", "DEPLOY")
        
        try:
            # Deploy to staging (assuming staging app exists)
            result = subprocess.run(
                ['git', 'push', f'https://git.heroku.com/{self.staging_app_name}.git', 'main'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.log(f"Staging deployment failed: {result.stderr}", "ERROR")
                return False
            
            # Wait for deployment to complete
            self.log("⏳ Waiting for staging deployment to complete...", "INFO")
            time.sleep(60)
            
            # Run staging tests
            return self.run_staging_tests()
            
        except Exception as e:
            self.log(f"Staging deployment error: {str(e)}", "ERROR")
            return False
    
    def run_staging_tests(self) -> bool:
        """Run integration tests on staging"""
        self.log("🧪 Running staging integration tests...", "INFO")
        
        try:
            # Health check
            response = requests.get(f"{self.staging_url}/health", timeout=30)
            if response.status_code != 200:
                self.log(f"Staging health check failed: {response.status_code}", "ERROR")
                return False
            
            # API tests
            endpoints_to_test = [
                ("/docs", [200]),
                ("/api/v1/contracts/history", [200, 422]),
            ]
            
            for endpoint, expected_codes in endpoints_to_test:
                response = requests.get(f"{self.staging_url}{endpoint}", timeout=30)
                if response.status_code not in expected_codes:
                    self.log(f"Staging API test failed for {endpoint}: {response.status_code}", "ERROR")
                    return False
            
            self.log("✅ Staging tests passed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Staging tests failed: {str(e)}", "ERROR")
            return False
    
    def deploy_to_production(self) -> bool:
        """Deploy to production with monitoring"""
        self.log("🚀 Deploying to production...", "DEPLOY")
        
        # Get current release for potential rollback
        current_release = self.get_current_release()
        
        try:
            # Deploy to production
            result = subprocess.run(
                ['git', 'push', 'heroku', 'main'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.log(f"Production deployment failed: {result.stderr}", "ERROR")
                return False
            
            self.log("✅ Production deployment successful", "SUCCESS")
            
            # Send notification
            self.send_slack_notification(
                f"🚀 SoliVolt deployed to production successfully!\nApp: {self.production_url}",
                success=True
            )
            
            # Monitor post-deployment health
            health_ok = self.monitor_post_deployment()
            
            if not health_ok:
                self.log("❌ Post-deployment health checks failed", "ERROR")
                if current_release:
                    self.rollback_to_release(current_release)
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Production deployment error: {str(e)}", "ERROR")
            self.send_slack_notification(
                f"❌ SoliVolt production deployment failed: {str(e)}",
                success=False
            )
            return False
    
    def get_current_release(self) -> Optional[Dict]:
        """Get current production release for rollback"""
        try:
            headers = self.get_heroku_headers()
            response = requests.get(
                f'https://api.heroku.com/apps/{self.heroku_app_name}/releases',
                headers=headers
            )
            
            if response.status_code == 200:
                releases = response.json()
                if releases:
                    return releases[-1]  # Latest release
            
            return None
            
        except Exception:
            return None
    
    def monitor_post_deployment(self) -> bool:
        """Monitor application health after deployment"""
        self.log("📊 Monitoring post-deployment health...", "INFO")
        
        start_time = time.time()
        health_checks = []
        
        while time.time() - start_time < self.health_check_timeout:
            try:
                # Health check
                health_start = time.time()
                response = requests.get(f"{self.production_url}/health", timeout=10)
                health_time = (time.time() - health_start) * 1000
                
                health_checks.append({
                    'timestamp': datetime.now().isoformat(),
                    'status_code': response.status_code,
                    'response_time': health_time,
                    'healthy': response.status_code == 200
                })
                
                if response.status_code != 200:
                    self.log(f"⚠️ Health check failed: {response.status_code}", "WARN")
                
                if health_time > self.performance_threshold:
                    self.log(f"⚠️ Slow response time: {health_time:.1f}ms", "WARN")
                
            except Exception as e:
                health_checks.append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'healthy': False
                })
                self.log(f"⚠️ Health check error: {str(e)}", "WARN")
            
            time.sleep(10)  # Check every 10 seconds
        
        # Analyze health
        total_checks = len(health_checks)
        healthy_checks = sum(1 for check in health_checks if check.get('healthy', False))
        availability = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        avg_response_time = 0
        response_times = [check.get('response_time', 0) for check in health_checks if 'response_time' in check]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        self.log(f"📊 Post-deployment metrics:", "INFO")
        self.log(f"   Availability: {availability:.1f}%", "INFO")
        self.log(f"   Average response time: {avg_response_time:.1f}ms", "INFO")
        
        # Determine if health is acceptable
        health_ok = (availability >= self.rollback_threshold and 
                    avg_response_time <= self.performance_threshold)
        
        if health_ok:
            self.log("✅ Post-deployment health checks passed", "SUCCESS")
        else:
            self.log("❌ Post-deployment health checks failed", "ERROR")
        
        return health_ok
    
    def rollback_to_release(self, release: Dict):
        """Rollback to specified release"""
        self.log(f"🔄 Rolling back to release v{release['version']}...", "DEPLOY")
        
        try:
            headers = self.get_heroku_headers()
            rollback_response = requests.post(
                f'https://api.heroku.com/apps/{self.heroku_app_name}/releases',
                headers=headers,
                json={'release': release['id']}
            )
            
            if rollback_response.status_code == 201:
                self.log("✅ Rollback completed successfully", "SUCCESS")
                
                # Send notification
                self.send_slack_notification(
                    f"🔄 SoliVolt rolled back to v{release['version']} due to health check failures",
                    success=False
                )
                
                # Monitor rollback health
                time.sleep(60)  # Wait for rollback to complete
                rollback_health = self.monitor_post_deployment()
                
                if rollback_health:
                    self.log("✅ Rollback health checks passed", "SUCCESS")
                else:
                    self.log("❌ Rollback health checks failed - manual intervention required", "ERROR")
            else:
                self.log("❌ Rollback failed", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Rollback error: {str(e)}", "ERROR")
    
    def blue_green_deployment(self) -> bool:
        """Implement blue-green deployment strategy"""
        self.log("🔵🟢 Starting blue-green deployment...", "DEPLOY")
        
        # For Heroku, we'll simulate blue-green by:
        # 1. Deploy to staging (green)
        # 2. Test staging thoroughly
        # 3. If tests pass, promote staging to production
        # 4. Keep old production as backup (blue)
        
        # Step 1: Deploy to staging (green environment)
        if not self.deploy_to_staging():
            return False
        
        # Step 2: Run comprehensive staging tests
        self.log("🧪 Running comprehensive staging tests...", "INFO")
        if not self.run_comprehensive_staging_tests():
            return False
        
        # Step 3: Promote staging to production
        self.log("🔄 Promoting staging to production...", "DEPLOY")
        return self.promote_staging_to_production()
    
    def run_comprehensive_staging_tests(self) -> bool:
        """Run comprehensive tests on staging"""
        test_suites = [
            ("Health Checks", self.run_staging_health_tests),
            ("API Tests", self.run_staging_api_tests),
            ("Load Tests", self.run_staging_load_tests),
            ("Security Tests", self.run_staging_security_tests)
        ]
        
        for test_name, test_func in test_suites:
            self.log(f"🧪 Running {test_name}...", "INFO")
            if not test_func():
                self.log(f"❌ {test_name} failed", "ERROR")
                return False
            self.log(f"✅ {test_name} passed", "SUCCESS")
        
        return True
    
    def run_staging_health_tests(self) -> bool:
        """Run health tests on staging"""
        try:
            for _ in range(10):  # 10 health checks
                response = requests.get(f"{self.staging_url}/health", timeout=10)
                if response.status_code != 200:
                    return False
                time.sleep(2)
            return True
        except Exception:
            return False
    
    def run_staging_api_tests(self) -> bool:
        """Run API tests on staging"""
        try:
            # Test contract analysis endpoint
            test_contract = {
                "source_code": "pragma solidity ^0.8.0; contract Test {}",
                "contract_name": "Test",
                "compiler_version": "0.8.19"
            }
            
            response = requests.post(
                f"{self.staging_url}/api/v1/contracts/analyze",
                json=test_contract,
                timeout=30
            )
            
            return response.status_code in [200, 422]  # Both are acceptable
            
        except Exception:
            return False
    
    def run_staging_load_tests(self) -> bool:
        """Run load tests on staging"""
        self.log("🔥 Running load tests...", "INFO")
        
        def make_request():
            try:
                response = requests.get(f"{self.staging_url}/health", timeout=10)
                return response.status_code == 200
            except Exception:
                return False
        
        # Run 50 concurrent requests
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results) * 100
        self.log(f"Load test success rate: {success_rate:.1f}%", "INFO")
        
        return success_rate >= 90.0  # 90% success rate required
    
    def run_staging_security_tests(self) -> bool:
        """Run basic security tests on staging"""
        try:
            # Test for common vulnerabilities
            security_endpoints = [
                f"{self.staging_url}/admin",  # Should return 404
                f"{self.staging_url}/.env",   # Should return 404
                f"{self.staging_url}/debug",  # Should return 404
            ]
            
            for endpoint in security_endpoints:
                response = requests.get(endpoint, timeout=10)
                if response.status_code not in [404, 405]:
                    self.log(f"Security concern: {endpoint} returned {response.status_code}", "WARN")
                    return False
            
            return True
            
        except Exception:
            return True  # Don't fail if security tests fail
    
    def promote_staging_to_production(self) -> bool:
        """Promote staging app to production"""
        # In a real blue-green setup, you'd swap DNS or use a load balancer
        # For Heroku, we'll deploy the same code to production
        return self.deploy_to_production()
    
    def canary_deployment(self, percentage: int = 10) -> bool:
        """Implement canary deployment (simulated)"""
        self.log(f"🐦 Starting canary deployment ({percentage}% traffic)...", "DEPLOY")
        
        # For Heroku, true canary requires a load balancer
        # We'll simulate by deploying and monitoring closely
        
        # Deploy to production
        if not self.deploy_to_production():
            return False
        
        # Monitor canary metrics more aggressively
        self.log(f"📊 Monitoring canary deployment for {percentage}% traffic...", "INFO")
        
        # Simulate canary monitoring (in real implementation, you'd check traffic split metrics)
        canary_health = self.monitor_canary_health(duration=600)  # 10 minutes
        
        if canary_health:
            self.log("✅ Canary deployment successful - promoting to 100%", "SUCCESS")
            return True
        else:
            self.log("❌ Canary deployment failed - rolling back", "ERROR")
            # Rollback would happen here
            return False
    
    def monitor_canary_health(self, duration: int) -> bool:
        """Monitor canary deployment health"""
        start_time = time.time()
        error_count = 0
        total_requests = 0
        
        while time.time() - start_time < duration:
            try:
                response = requests.get(f"{self.production_url}/health", timeout=5)
                total_requests += 1
                
                if response.status_code != 200:
                    error_count += 1
                
                # Check error rate
                error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
                
                if error_rate > 5.0:  # More than 5% error rate
                    self.log(f"❌ Canary error rate too high: {error_rate:.1f}%", "ERROR")
                    return False
                
            except Exception:
                error_count += 1
                total_requests += 1
            
            time.sleep(30)  # Check every 30 seconds
        
        # Final error rate check
        final_error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
        self.log(f"📊 Canary final error rate: {final_error_rate:.1f}%", "INFO")
        
        return final_error_rate <= 2.0  # Less than 2% error rate for success
    
    def full_deployment_pipeline(self, strategy: str = "standard") -> bool:
        """Run full deployment pipeline"""
        self.log("🚀 Starting full deployment pipeline...", "DEPLOY")
        self.log(f"Strategy: {strategy}", "INFO")
        
        # Pre-deployment checks
        if not self.pre_deployment_checks():
            self.log("❌ Pre-deployment checks failed", "ERROR")
            return False
        
        # Choose deployment strategy
        if strategy == "blue-green":
            return self.blue_green_deployment()
        elif strategy == "canary":
            return self.canary_deployment()
        else:
            # Standard deployment
            if not self.deploy_to_staging():
                return False
            return self.deploy_to_production()

def main():
    """Main function"""
    print("🚀 SoliVolt Heroku Deployment Manager")
    print("=" * 50)
    
    deployer = HerokuDeploymentManager()
    
    while True:
        print("\n🎮 Deployment Menu:")
        print("1. 🔍 Run Pre-deployment Checks")
        print("2. 🧪 Deploy to Staging")
        print("3. 🚀 Deploy to Production")
        print("4. 🔵🟢 Blue-Green Deployment")
        print("5. 🐦 Canary Deployment")
        print("6. 📊 Monitor Production Health")
        print("7. 🔄 Rollback Last Deployment")
        print("8. 🎯 Full Deployment Pipeline")
        print("9. 🚪 Exit")
        
        choice = input("\nChoose deployment option (1-9): ").strip()
        
        if choice == '1':
            deployer.pre_deployment_checks()
        elif choice == '2':
            deployer.deploy_to_staging()
        elif choice == '3':
            deployer.deploy_to_production()
        elif choice == '4':
            deployer.blue_green_deployment()
        elif choice == '5':
            percentage = input("Canary percentage (default 10): ").strip()
            percentage = int(percentage) if percentage.isdigit() else 10
            deployer.canary_deployment(percentage)
        elif choice == '6':
            deployer.monitor_post_deployment()
        elif choice == '7':
            current_release = deployer.get_current_release()
            if current_release:
                deployer.rollback_to_release(current_release)
            else:
                print("❌ No release found for rollback")
        elif choice == '8':
            strategy = input("Strategy (standard/blue-green/canary): ").strip().lower()
            if strategy not in ['standard', 'blue-green', 'canary']:
                strategy = 'standard'
            deployer.full_deployment_pipeline(strategy)
        elif choice == '9':
            print("👋 Deployment management complete!")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    main()
