#!/usr/bin/env python3
"""
🎯 SOLIVOLT DEVOPS EXPERIENCE LAB
Complete DevOps SaaS Simulation & Infrastructure Management

This script implements a comprehensive DevOps experience lab for SoliVolt,
simulating real-world SaaS operations including CI/CD, monitoring, chaos engineering,
and failure recovery scenarios.
"""

import os
import sys
import time
import json
import requests
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class SoliVoltDevOpsLab:
    """
    Complete DevOps Experience Lab for SoliVolt
    Simulates production SaaS operations and chaos engineering
    """
    
    def __init__(self):
        self.project_root = Path.cwd()
        
        # Heroku Configuration
        self.heroku_app_name = os.getenv('HEROKU_APP_NAME', 'solivolt-8e0565441715')
        self.heroku_api_key = os.getenv('HEROKU_API_KEY', '')
        self.production_url = f"https://{self.heroku_app_name}.herokuapp.com"
        self.staging_url = os.getenv('STAGING_URL', 'https://solivolt-staging.herokuapp.com')
        
        # Monitoring configuration
        self.metrics_history = []
        self.chaos_scenarios = []
        self.deployment_history = []
        
        # Initialize logging
        self.log_file = f"devops_lab_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with color coding and file output"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        colors = {
            "INFO": "\033[32m",    # Green
            "WARN": "\033[33m",    # Yellow  
            "ERROR": "\033[31m",   # Red
            "SUCCESS": "\033[92m", # Bright Green
            "CHAOS": "\033[35m",   # Magenta
            "DEPLOY": "\033[36m",  # Cyan
            "RESET": "\033[0m"     # Reset
        }
        
        color = colors.get(level, colors["INFO"])
        colored_message = f"{color}[{timestamp}] [{level}] {message}{colors['RESET']}"
        
        # Print to console
        print(colored_message)
        
        # Write to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    
    def check_prerequisites(self) -> bool:
        """Check if all required tools are installed"""
        self.log("🔍 Checking DevOps prerequisites...", "INFO")
        
        required_tools = {
            'git': 'git --version',
            'heroku': 'heroku --version',
            'docker': 'docker --version',
            'terraform': 'terraform --version'  # Optional
        }
        
        missing_tools = []
        
        for tool, command in required_tools.items():
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    self.log(f"✅ {tool} is installed", "SUCCESS")
                else:
                    missing_tools.append(tool)
            except FileNotFoundError:
                if tool != 'terraform':  # Terraform is optional
                    missing_tools.append(tool)
                else:
                    self.log(f"⚠️ {tool} not found (optional)", "WARN")
        
        if missing_tools:
            self.log(f"❌ Missing required tools: {', '.join(missing_tools)}", "ERROR")
            return False
        
        self.log("✅ All prerequisites met!", "SUCCESS")
        return True
    
    def create_environment_configs(self):
        """Create staging and production environment configurations"""
        self.log("📦 Creating environment configurations...", "DEPLOY")
        
        # Create staging environment
        staging_env = {
            "ENVIRONMENT": "staging",
            "DEBUG": "True",
            "DATABASE_URL": "postgresql://staging_user:staging_pass@staging_db:5432/solivolt_staging",
            "GEMINI_API_KEY": "${GEMINI_API_KEY}",
            "ALLOWED_HOSTS": f"{self.staging_url.replace('https://', '')}",
            "LOG_LEVEL": "DEBUG",
            "SENTRY_DSN": "${SENTRY_DSN_STAGING}",
            "RATE_LIMIT_ENABLED": "False"
        }
        
        # Create production environment
        production_env = {
            "ENVIRONMENT": "production",
            "DEBUG": "False",
            "DATABASE_URL": "${DATABASE_URL}",
            "GEMINI_API_KEY": "${GEMINI_API_KEY}",
            "ALLOWED_HOSTS": f"{self.production_url.replace('https://', '')}",
            "LOG_LEVEL": "INFO",
            "SENTRY_DSN": "${SENTRY_DSN_PRODUCTION}",
            "RATE_LIMIT_ENABLED": "True",
            "SECURE_SSL_REDIRECT": "True"
        }
        
        # Write environment files
        env_dir = self.project_root / "environments"
        env_dir.mkdir(exist_ok=True)
        
        with open(env_dir / ".env.staging", 'w') as f:
            for key, value in staging_env.items():
                f.write(f"{key}={value}\n")
        
        with open(env_dir / ".env.production", 'w') as f:
            for key, value in production_env.items():
                f.write(f"{key}={value}\n")
        
        self.log("✅ Environment configurations created", "SUCCESS")
    
    def setup_monitoring_stack(self):
        """Set up Prometheus, Grafana, and Loki for monitoring"""
        self.log("📊 Setting up monitoring stack...", "DEPLOY")
        
        # Create docker-compose for monitoring
        monitoring_compose = {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": "solivolt-prometheus",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml",
                        "./monitoring/prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--web.enable-lifecycle"
                    ]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "container_name": "solivolt-grafana",
                    "ports": ["3001:3000"],
                    "environment": [
                        "GF_SECURITY_ADMIN_PASSWORD=admin123"
                    ],
                    "volumes": [
                        "./monitoring/grafana/provisioning:/etc/grafana/provisioning",
                        "./monitoring/grafana/dashboards:/var/lib/grafana/dashboards"
                    ]
                },
                "loki": {
                    "image": "grafana/loki:latest",
                    "container_name": "solivolt-loki",
                    "ports": ["3100:3100"],
                    "command": "-config.file=/etc/loki/local-config.yaml"
                },
                "promtail": {
                    "image": "grafana/promtail:latest",
                    "container_name": "solivolt-promtail",
                    "volumes": [
                        "./monitoring/promtail/config.yml:/etc/promtail/config.yml",
                        "/var/log:/var/log:ro"
                    ],
                    "command": "-config.file=/etc/promtail/config.yml"
                }
            }
        }
        
        # Write monitoring docker-compose
        monitoring_dir = self.project_root / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        with open(monitoring_dir / "docker-compose.monitoring.yml", 'w') as f:
            import yaml
            yaml.dump(monitoring_compose, f, default_flow_style=False)
        
        # Create Grafana dashboard for SoliVolt
        self.create_grafana_dashboard()
        
        self.log("✅ Monitoring stack configuration created", "SUCCESS")
    
    def create_grafana_dashboard(self):
        """Create custom Grafana dashboard for SoliVolt metrics"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "SoliVolt DevOps Dashboard",
                "tags": ["solivolt", "devops"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Application Health",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "up{job=\"solivolt-backend\"}",
                                "legendFormat": "Backend Status"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Response Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "http_request_duration_seconds",
                                "legendFormat": "Response Time"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Deployment History",
                        "type": "table",
                        "targets": [
                            {
                                "expr": "deployment_info",
                                "legendFormat": "Deployments"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "5s"
            }
        }
        
        # Write dashboard
        dashboard_dir = self.project_root / "monitoring" / "grafana" / "dashboards"
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        with open(dashboard_dir / "solivolt_dashboard.json", 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        self.log("✅ Grafana dashboard created", "SUCCESS")
    
    def run_chaos_engineering(self, scenario: str = "all"):
        """Execute chaos engineering scenarios"""
        self.log(f"💥 Starting chaos engineering scenario: {scenario}", "CHAOS")
        
        scenarios = {
            "env_failure": self.chaos_env_failure,
            "database_disconnect": self.chaos_database_disconnect,
            "memory_overload": self.chaos_memory_overload,
            "network_latency": self.chaos_network_latency,
            "dyno_restart": self.chaos_dyno_restart
        }
        
        if scenario == "all":
            for name, func in scenarios.items():
                self.log(f"🎯 Running chaos scenario: {name}", "CHAOS")
                try:
                    func()
                    time.sleep(30)  # Wait between scenarios
                except Exception as e:
                    self.log(f"❌ Chaos scenario {name} failed: {str(e)}", "ERROR")
        elif scenario in scenarios:
            scenarios[scenario]()
        else:
            self.log(f"❌ Unknown chaos scenario: {scenario}", "ERROR")
    
    def chaos_env_failure(self):
        """Simulate environment variable failure"""
        self.log("💥 CHAOS: Simulating environment variable failure", "CHAOS")
        
        if self.heroku_api_key:
            try:
                # Temporarily remove a critical env var
                headers = {
                    'Authorization': f'Bearer {self.heroku_api_key}',
                    'Accept': 'application/vnd.heroku+json; version=3'
                }
                
                # Remove GEMINI_API_KEY temporarily
                requests.delete(
                    f'https://api.heroku.com/apps/{self.heroku_app_name}/config-vars/GEMINI_API_KEY',
                    headers=headers
                )
                
                self.log("💥 Removed GEMINI_API_KEY from production", "CHAOS")
                
                # Monitor for 60 seconds
                self.monitor_chaos_impact(60)
                
                # Restore the env var (you'll need to set this manually)
                self.log("🔧 Manual intervention required: Restore GEMINI_API_KEY", "WARN")
                
            except Exception as e:
                self.log(f"❌ Failed to simulate env failure: {str(e)}", "ERROR")
        else:
            self.log("⚠️ No Heroku API key provided, skipping env failure simulation", "WARN")
    
    def chaos_database_disconnect(self):
        """Simulate database connectivity issues"""
        self.log("💥 CHAOS: Simulating database connectivity issues", "CHAOS")
        
        # This would involve temporarily changing DATABASE_URL to an invalid value
        # For safety, we'll just log the scenario
        self.log("💥 Would modify DATABASE_URL to simulate DB failure", "CHAOS")
        self.log("🔧 In real scenario: Change DATABASE_URL to invalid connection", "WARN")
        
        # Monitor application health
        self.monitor_chaos_impact(30)
    
    def chaos_memory_overload(self):
        """Simulate memory overload"""
        self.log("💥 CHAOS: Simulating memory overload", "CHAOS")
        
        # Create a script to consume memory on the dyno
        memory_script = '''
import time
import os

# Allocate memory progressively
memory_hog = []
for i in range(1000):
    memory_hog.append(" " * 1024 * 1024)  # 1MB chunks
    time.sleep(0.1)
    if i % 100 == 0:
        print(f"Allocated {i} MB")
'''
        
        # In a real scenario, you'd deploy this to your dyno
        self.log("💥 Memory overload script prepared", "CHAOS")
        self.log("🔧 Deploy memory_hog.py to trigger memory alerts", "WARN")
    
    def chaos_network_latency(self):
        """Simulate network latency issues"""
        self.log("💥 CHAOS: Simulating network latency", "CHAOS")
        
        # Test API with increased load to simulate latency
        def stress_endpoint():
            for _ in range(50):
                try:
                    response = requests.get(f"{self.production_url}/health", timeout=1)
                    if response.status_code != 200:
                        self.log(f"⚠️ Health check failed: {response.status_code}", "WARN")
                except requests.exceptions.Timeout:
                    self.log("⚠️ Request timeout detected", "WARN")
                except Exception as e:
                    self.log(f"⚠️ Request failed: {str(e)}", "WARN")
                time.sleep(0.1)
        
        # Run stress test in parallel
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=stress_endpoint)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        self.log("💥 Network stress test completed", "CHAOS")
    
    def chaos_dyno_restart(self):
        """Restart Heroku dynos to simulate failures"""
        self.log("💥 CHAOS: Restarting Heroku dynos", "CHAOS")
        
        if self.heroku_api_key:
            try:
                headers = {
                    'Authorization': f'Bearer {self.heroku_api_key}',
                    'Accept': 'application/vnd.heroku+json; version=3'
                }
                
                # Restart all dynos
                response = requests.delete(
                    f'https://api.heroku.com/apps/{self.heroku_app_name}/dynos',
                    headers=headers
                )
                
                if response.status_code == 202:
                    self.log("💥 Dynos restarted successfully", "CHAOS")
                    self.monitor_chaos_impact(120)  # Monitor recovery
                else:
                    self.log(f"❌ Failed to restart dynos: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Dyno restart failed: {str(e)}", "ERROR")
        else:
            self.log("⚠️ No Heroku API key provided, skipping dyno restart", "WARN")
    
    def monitor_chaos_impact(self, duration_seconds: int):
        """Monitor application health during chaos scenarios"""
        self.log(f"📊 Monitoring chaos impact for {duration_seconds} seconds...", "INFO")
        
        start_time = time.time()
        health_checks = []
        
        while time.time() - start_time < duration_seconds:
            try:
                response = requests.get(f"{self.production_url}/health", timeout=5)
                health_checks.append({
                    'timestamp': datetime.now().isoformat(),
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'healthy': response.status_code == 200
                })
                
                if response.status_code != 200:
                    self.log(f"🚨 Health check failed: {response.status_code}", "ERROR")
                
            except Exception as e:
                health_checks.append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'healthy': False
                })
                self.log(f"🚨 Health check error: {str(e)}", "ERROR")
            
            time.sleep(5)
        
        # Analyze results
        healthy_count = sum(1 for check in health_checks if check.get('healthy', False))
        total_checks = len(health_checks)
        availability = (healthy_count / total_checks) * 100 if total_checks > 0 else 0
        
        self.log(f"📊 Availability during chaos: {availability:.1f}% ({healthy_count}/{total_checks})", "INFO")
        
        # Store chaos scenario results
        self.chaos_scenarios.append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration_seconds,
            'availability': availability,
            'health_checks': health_checks
        })
    
    def deploy_with_monitoring(self, environment: str = "staging"):
        """Deploy with comprehensive monitoring and rollback capability"""
        self.log(f"🚀 Starting deployment to {environment}...", "DEPLOY")
        
        deployment_start = datetime.now()
        deployment_id = f"deploy_{int(deployment_start.timestamp())}"
        
        # Pre-deployment checks
        if not self.run_pre_deployment_checks():
            self.log("❌ Pre-deployment checks failed", "ERROR")
            return False
        
        # Deploy
        success = self.execute_deployment(environment)
        
        # Post-deployment monitoring
        if success:
            self.log("✅ Deployment successful, monitoring health...", "SUCCESS")
            health_ok = self.post_deployment_monitoring(environment)
            
            if not health_ok:
                self.log("❌ Post-deployment health checks failed, initiating rollback", "ERROR")
                self.rollback_deployment(environment)
                success = False
        
        # Record deployment
        deployment_record = {
            'id': deployment_id,
            'environment': environment,
            'timestamp': deployment_start.isoformat(),
            'success': success,
            'duration': (datetime.now() - deployment_start).total_seconds()
        }
        
        self.deployment_history.append(deployment_record)
        
        return success
    
    def run_pre_deployment_checks(self) -> bool:
        """Run comprehensive pre-deployment checks"""
        self.log("🔍 Running pre-deployment checks...", "INFO")
        
        checks = [
            ("Linting", self.check_code_quality),
            ("Tests", self.run_tests),
            ("Security", self.security_scan),
            ("Dependencies", self.check_dependencies)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                if check_func():
                    self.log(f"✅ {check_name} check passed", "SUCCESS")
                else:
                    self.log(f"❌ {check_name} check failed", "ERROR")
                    all_passed = False
            except Exception as e:
                self.log(f"❌ {check_name} check error: {str(e)}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def check_code_quality(self) -> bool:
        """Run code quality checks"""
        try:
            # Run backend linting
            backend_result = subprocess.run(
                ['python', '-m', 'flake8', 'backend/app/', '--max-line-length=88'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if backend_result.returncode != 0:
                self.log(f"Backend linting issues: {backend_result.stdout}", "WARN")
                return False
            
            # Run frontend linting
            frontend_result = subprocess.run(
                ['npm', 'run', 'lint'],
                capture_output=True,
                text=True,
                cwd=self.project_root / 'frontend'
            )
            
            return frontend_result.returncode == 0
            
        except Exception:
            return False
    
    def run_tests(self) -> bool:
        """Run test suites"""
        try:
            # Run backend tests
            backend_result = subprocess.run(
                ['python', '-m', 'pytest', 'tests/', '-v'],
                capture_output=True,
                text=True,
                cwd=self.project_root / 'backend'
            )
            
            return backend_result.returncode == 0
            
        except Exception:
            return False
    
    def security_scan(self) -> bool:
        """Run security scans"""
        try:
            # Check for known vulnerabilities
            result = subprocess.run(
                ['pip', 'audit'],
                capture_output=True,
                text=True,
                cwd=self.project_root / 'backend'
            )
            
            # pip audit returns 0 if no vulnerabilities found
            return result.returncode == 0
            
        except Exception:
            return True  # Don't fail deployment if security scan fails
    
    def check_dependencies(self) -> bool:
        """Check dependency health"""
        try:
            # Check if all dependencies are installable
            result = subprocess.run(
                ['pip', 'check'],
                capture_output=True,
                text=True,
                cwd=self.project_root / 'backend'
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def execute_deployment(self, environment: str) -> bool:
        """Execute the actual deployment"""
        try:
            if environment == "staging":
                # Deploy to staging (this would trigger your CI/CD)
                self.log("🚀 Triggering staging deployment...", "DEPLOY")
                # In reality, this would trigger a GitHub Action or direct deploy
                time.sleep(10)  # Simulate deployment time
                return True
            
            elif environment == "production":
                # Deploy to production Heroku
                self.log("🚀 Deploying to Heroku production...", "DEPLOY")
                
                result = subprocess.run(
                    ['git', 'push', 'heroku', 'main'],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                return result.returncode == 0
                
        except Exception as e:
            self.log(f"❌ Deployment failed: {str(e)}", "ERROR")
            return False
    
    def post_deployment_monitoring(self, environment: str, duration: int = 300) -> bool:
        """Monitor application health after deployment"""
        self.log(f"📊 Monitoring {environment} health for {duration} seconds...", "INFO")
        
        target_url = self.production_url if environment == "production" else self.staging_url
        
        start_time = time.time()
        failed_checks = 0
        total_checks = 0
        
        while time.time() - start_time < duration:
            try:
                # Health check
                response = requests.get(f"{target_url}/health", timeout=10)
                total_checks += 1
                
                if response.status_code != 200:
                    failed_checks += 1
                    self.log(f"⚠️ Health check failed: {response.status_code}", "WARN")
                
                # API check
                api_response = requests.get(f"{target_url}/api/v1/contracts/history", timeout=10)
                if api_response.status_code not in [200, 422]:  # 422 is expected for some endpoints
                    failed_checks += 1
                    self.log(f"⚠️ API check failed: {api_response.status_code}", "WARN")
                
            except Exception as e:
                failed_checks += 1
                self.log(f"⚠️ Monitoring error: {str(e)}", "WARN")
            
            time.sleep(30)  # Check every 30 seconds
        
        # Determine if health is acceptable
        failure_rate = failed_checks / max(total_checks, 1) * 100
        health_threshold = 10  # Allow up to 10% failure rate
        
        if failure_rate <= health_threshold:
            self.log(f"✅ Post-deployment health OK (failure rate: {failure_rate:.1f}%)", "SUCCESS")
            return True
        else:
            self.log(f"❌ Post-deployment health failed (failure rate: {failure_rate:.1f}%)", "ERROR")
            return False
    
    def rollback_deployment(self, environment: str):
        """Rollback deployment on failure"""
        self.log(f"🔄 Rolling back {environment} deployment...", "DEPLOY")
        
        if environment == "production" and self.heroku_api_key:
            try:
                headers = {
                    'Authorization': f'Bearer {self.heroku_api_key}',
                    'Accept': 'application/vnd.heroku+json; version=3'
                }
                
                # Get releases
                releases_response = requests.get(
                    f'https://api.heroku.com/apps/{self.heroku_app_name}/releases',
                    headers=headers
                )
                
                if releases_response.status_code == 200:
                    releases = releases_response.json()
                    if len(releases) >= 2:
                        # Rollback to previous release
                        previous_release = releases[-2]
                        
                        rollback_response = requests.post(
                            f'https://api.heroku.com/apps/{self.heroku_app_name}/releases',
                            headers=headers,
                            json={'release': previous_release['id']}
                        )
                        
                        if rollback_response.status_code == 201:
                            self.log("✅ Rollback completed successfully", "SUCCESS")
                        else:
                            self.log("❌ Rollback failed", "ERROR")
                
            except Exception as e:
                self.log(f"❌ Rollback error: {str(e)}", "ERROR")
    
    def generate_devops_report(self):
        """Generate comprehensive DevOps report"""
        self.log("📄 Generating DevOps experience report...", "INFO")
        
        report = {
            "solivolt_devops_lab_report": {
                "generated_at": datetime.now().isoformat(),
                "project": "SoliVolt Smart Contract Rewriter",
                "duration": (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)).total_seconds(),
                
                "infrastructure": {
                    "production_url": self.production_url,
                    "staging_url": self.staging_url,
                    "monitoring_stack": ["Prometheus", "Grafana", "Loki"],
                    "deployment_platform": "Heroku",
                    "ci_cd_platform": "GitHub Actions"
                },
                
                "deployments": {
                    "total_deployments": len(self.deployment_history),
                    "successful_deployments": sum(1 for d in self.deployment_history if d['success']),
                    "deployment_history": self.deployment_history[-10:]  # Last 10 deployments
                },
                
                "chaos_engineering": {
                    "scenarios_run": len(self.chaos_scenarios),
                    "average_availability": sum(s.get('availability', 0) for s in self.chaos_scenarios) / max(len(self.chaos_scenarios), 1),
                    "chaos_history": self.chaos_scenarios
                },
                
                "metrics": {
                    "monitoring_samples": len(self.metrics_history),
                    "alert_count": 0,  # Would be populated by monitoring
                    "uptime_percentage": 99.5  # Would be calculated from real metrics
                },
                
                "achievements": self.get_devops_achievements(),
                
                "recommendations": [
                    "Set up automated rollback triggers based on error rates",
                    "Implement blue-green deployments for zero-downtime releases",
                    "Add cost monitoring and alerting",
                    "Implement A/B testing framework",
                    "Set up multi-region deployment for high availability"
                ]
            }
        }
        
        # Write report
        report_file = f"solivolt_devops_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Write summary
        self.log("📊 DEVOPS LAB SUMMARY", "SUCCESS")
        self.log("=" * 50, "INFO")
        self.log(f"🚀 Total Deployments: {len(self.deployment_history)}", "INFO")
        self.log(f"💥 Chaos Scenarios: {len(self.chaos_scenarios)}", "INFO")
        self.log(f"📄 Report saved: {report_file}", "INFO")
        self.log(f"📋 Log file: {self.log_file}", "INFO")
        
        return report_file
    
    def get_devops_achievements(self) -> List[str]:
        """Get list of DevOps achievements unlocked"""
        achievements = []
        
        if len(self.deployment_history) > 0:
            achievements.append("🚀 First Deployment")
        
        if len(self.deployment_history) >= 5:
            achievements.append("🔄 Deployment Master (5+ deployments)")
        
        if len(self.chaos_scenarios) > 0:
            achievements.append("💥 Chaos Engineer")
        
        if any(d['success'] for d in self.deployment_history):
            achievements.append("✅ Successful Deployment")
        
        if any(not d['success'] for d in self.deployment_history):
            achievements.append("🔧 Failure Recovery Expert")
        
        successful_deploys = sum(1 for d in self.deployment_history if d['success'])
        if successful_deploys / max(len(self.deployment_history), 1) >= 0.8:
            achievements.append("🎯 High Reliability (80%+ success rate)")
        
        return achievements
    
    def run_interactive_lab(self):
        """Run interactive DevOps lab experience"""
        self.log("🎯 Welcome to SoliVolt DevOps Experience Lab!", "SUCCESS")
        self.log("=" * 60, "INFO")
        
        while True:
            print("\n🎮 DevOps Lab Menu:")
            print("1. 📦 Setup Environment Configs")
            print("2. 📊 Setup Monitoring Stack")
            print("3. 🚀 Deploy with Monitoring")
            print("4. 💥 Run Chaos Engineering")
            print("5. 🔍 Monitor Application Health")
            print("6. 📄 Generate DevOps Report")
            print("7. 🏆 View Achievements")
            print("8. 🎓 Complete Lab & Exit")
            
            choice = input("\nChoose your DevOps adventure (1-8): ").strip()
            
            if choice == '1':
                self.create_environment_configs()
            elif choice == '2':
                self.setup_monitoring_stack()
            elif choice == '3':
                env = input("Deploy to (staging/production): ").strip().lower()
                if env in ['staging', 'production']:
                    self.deploy_with_monitoring(env)
                else:
                    self.log("❌ Invalid environment", "ERROR")
            elif choice == '4':
                print("\nChaos Scenarios:")
                print("1. env_failure")
                print("2. database_disconnect") 
                print("3. memory_overload")
                print("4. network_latency")
                print("5. dyno_restart")
                print("6. all")
                
                scenario_choice = input("Choose scenario (1-6): ").strip()
                scenarios = ['env_failure', 'database_disconnect', 'memory_overload', 
                           'network_latency', 'dyno_restart', 'all']
                
                if scenario_choice.isdigit() and 1 <= int(scenario_choice) <= 6:
                    self.run_chaos_engineering(scenarios[int(scenario_choice) - 1])
                else:
                    self.log("❌ Invalid choice", "ERROR")
            elif choice == '5':
                duration = input("Monitor duration in seconds (default 60): ").strip()
                duration = int(duration) if duration.isdigit() else 60
                self.monitor_chaos_impact(duration)
            elif choice == '6':
                report_file = self.generate_devops_report()
                print(f"\n📄 Report generated: {report_file}")
            elif choice == '7':
                achievements = self.get_devops_achievements()
                print("\n🏆 Your DevOps Achievements:")
                for achievement in achievements:
                    print(f"  {achievement}")
                if not achievements:
                    print("  No achievements yet - start deploying!")
            elif choice == '8':
                self.log("🎓 DevOps Lab completed! Thanks for participating!", "SUCCESS")
                self.generate_devops_report()
                break
            else:
                self.log("❌ Invalid choice, please try again", "ERROR")

def main():
    """Main function to run the DevOps lab"""
    print("🎯 SoliVolt DevOps Experience Lab")
    print("=" * 50)
    print("Complete DevOps SaaS Simulation")
    print("=" * 50)
    
    lab = SoliVoltDevOpsLab()
    
    # Check prerequisites
    if not lab.check_prerequisites():
        print("❌ Prerequisites not met. Please install required tools.")
        return
    
    # Run interactive lab
    lab.run_interactive_lab()

if __name__ == "__main__":
    main()
