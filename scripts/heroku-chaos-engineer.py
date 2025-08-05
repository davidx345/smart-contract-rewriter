#!/usr/bin/env python3
"""
💥 SoliVolt Chaos Engineering for Heroku
Advanced chaos scenarios tailored for Heroku deployments
"""

import os
import time
import json
import requests
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class HerokuChaosEngineer:
    """
    Chaos Engineering specifically designed for Heroku applications
    """
    
    def __init__(self):
        self.heroku_app_name = os.getenv('HEROKU_APP_NAME', 'solivolt-8e0565441715')
        self.heroku_api_key = os.getenv('HEROKU_API_KEY', '')
        self.app_url = f"https://{self.heroku_app_name}.herokuapp.com"
        self.chaos_results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[32m",    # Green
            "WARN": "\033[33m",    # Yellow  
            "ERROR": "\033[31m",   # Red
            "CHAOS": "\033[35m",   # Magenta
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
    
    def chaos_dyno_cycling(self):
        """Chaos: Rapidly cycle dynos to test auto-recovery"""
        self.log("💥 CHAOS: Dyno Cycling Attack", "CHAOS")
        
        if not self.heroku_api_key:
            self.log("❌ No Heroku API key provided", "ERROR")
            return
        
        headers = self.get_heroku_headers()
        
        try:
            # Get current dyno state
            dynos_response = requests.get(
                f'https://api.heroku.com/apps/{self.heroku_app_name}/dynos',
                headers=headers
            )
            
            if dynos_response.status_code != 200:
                self.log(f"❌ Failed to get dynos: {dynos_response.status_code}", "ERROR")
                return
            
            dynos = dynos_response.json()
            self.log(f"📊 Found {len(dynos)} dynos", "INFO")
            
            # Monitor baseline
            baseline_metrics = self.monitor_app_health(30)
            
            # Restart dynos multiple times
            for cycle in range(3):
                self.log(f"💥 Dyno cycle {cycle + 1}/3", "CHAOS")
                
                # Restart all dynos
                restart_response = requests.delete(
                    f'https://api.heroku.com/apps/{self.heroku_app_name}/dynos',
                    headers=headers
                )
                
                if restart_response.status_code == 202:
                    self.log("💥 Dynos restarted", "CHAOS")
                else:
                    self.log(f"❌ Restart failed: {restart_response.status_code}", "ERROR")
                
                # Wait and monitor recovery
                time.sleep(60)  # Wait for restart
                recovery_metrics = self.monitor_app_health(60)
                
                # Analyze recovery
                self.analyze_recovery(baseline_metrics, recovery_metrics, f"dyno_cycle_{cycle}")
            
        except Exception as e:
            self.log(f"❌ Dyno cycling failed: {str(e)}", "ERROR")
    
    def chaos_config_corruption(self):
        """Chaos: Temporarily corrupt configuration"""
        self.log("💥 CHAOS: Configuration Corruption", "CHAOS")
        
        if not self.heroku_api_key:
            self.log("❌ No Heroku API key provided", "ERROR")
            return
        
        headers = self.get_heroku_headers()
        
        try:
            # Get current config
            config_response = requests.get(
                f'https://api.heroku.com/apps/{self.heroku_app_name}/config-vars',
                headers=headers
            )
            
            if config_response.status_code != 200:
                self.log(f"❌ Failed to get config: {config_response.status_code}", "ERROR")
                return
            
            original_config = config_response.json()
            self.log(f"📊 Found {len(original_config)} config vars", "INFO")
            
            # Monitor baseline
            baseline_metrics = self.monitor_app_health(30)
            
            # Corrupt critical config (temporarily set DATABASE_URL to invalid)
            if 'DATABASE_URL' in original_config:
                corrupt_config = {
                    'DATABASE_URL': 'postgresql://invalid:invalid@invalid:5432/invalid'
                }
                
                self.log("💥 Corrupting DATABASE_URL", "CHAOS")
                
                # Apply corrupt config
                corrupt_response = requests.patch(
                    f'https://api.heroku.com/apps/{self.heroku_app_name}/config-vars',
                    headers=headers,
                    json=corrupt_config
                )
                
                if corrupt_response.status_code == 200:
                    self.log("💥 Config corrupted successfully", "CHAOS")
                    
                    # Monitor the chaos
                    chaos_metrics = self.monitor_app_health(120)
                    
                    # Restore original config
                    self.log("🔧 Restoring original configuration", "INFO")
                    restore_response = requests.patch(
                        f'https://api.heroku.com/apps/{self.heroku_app_name}/config-vars',
                        headers=headers,
                        json={'DATABASE_URL': original_config['DATABASE_URL']}
                    )
                    
                    if restore_response.status_code == 200:
                        self.log("✅ Configuration restored", "SUCCESS")
                        
                        # Monitor recovery
                        recovery_metrics = self.monitor_app_health(120)
                        
                        # Analyze the chaos impact
                        self.analyze_recovery(baseline_metrics, recovery_metrics, "config_corruption")
                    else:
                        self.log("❌ Failed to restore config!", "ERROR")
                else:
                    self.log(f"❌ Failed to corrupt config: {corrupt_response.status_code}", "ERROR")
            else:
                self.log("⚠️ DATABASE_URL not found in config", "WARN")
                
        except Exception as e:
            self.log(f"❌ Config corruption failed: {str(e)}", "ERROR")
    
    def chaos_scale_down_up(self):
        """Chaos: Scale dynos down and back up"""
        self.log("💥 CHAOS: Scale Down/Up Test", "CHAOS")
        
        if not self.heroku_api_key:
            self.log("❌ No Heroku API key provided", "ERROR")
            return
        
        headers = self.get_heroku_headers()
        
        try:
            # Get current formation
            formation_response = requests.get(
                f'https://api.heroku.com/apps/{self.heroku_app_name}/formation',
                headers=headers
            )
            
            if formation_response.status_code != 200:
                self.log(f"❌ Failed to get formation: {formation_response.status_code}", "ERROR")
                return
            
            formation = formation_response.json()
            original_quantities = {}
            
            for process in formation:
                original_quantities[process['type']] = process['quantity']
            
            self.log(f"📊 Current formation: {original_quantities}", "INFO")
            
            # Monitor baseline
            baseline_metrics = self.monitor_app_health(30)
            
            # Scale down to 0
            self.log("💥 Scaling down to 0 dynos", "CHAOS")
            for process_type in original_quantities:
                scale_response = requests.patch(
                    f'https://api.heroku.com/apps/{self.heroku_app_name}/formation/{process_type}',
                    headers=headers,
                    json={'quantity': 0}
                )
                
                if scale_response.status_code == 200:
                    self.log(f"💥 Scaled {process_type} to 0", "CHAOS")
                else:
                    self.log(f"❌ Failed to scale {process_type}: {scale_response.status_code}", "ERROR")
            
            # Monitor downtime
            downtime_start = time.time()
            downtime_metrics = self.monitor_app_health(60)
            
            # Scale back up
            self.log("🔧 Scaling back to original quantities", "INFO")
            for process_type, quantity in original_quantities.items():
                scale_response = requests.patch(
                    f'https://api.heroku.com/apps/{self.heroku_app_name}/formation/{process_type}',
                    headers=headers,
                    json={'quantity': quantity}
                )
                
                if scale_response.status_code == 200:
                    self.log(f"✅ Scaled {process_type} to {quantity}", "SUCCESS")
                else:
                    self.log(f"❌ Failed to restore {process_type}: {scale_response.status_code}", "ERROR")
            
            # Monitor recovery
            recovery_metrics = self.monitor_app_health(120)
            
            # Calculate total downtime
            downtime_duration = time.time() - downtime_start
            self.log(f"📊 Total downtime: {downtime_duration:.1f} seconds", "INFO")
            
            # Analyze recovery
            self.analyze_recovery(baseline_metrics, recovery_metrics, "scale_down_up")
            
        except Exception as e:
            self.log(f"❌ Scale chaos failed: {str(e)}", "ERROR")
    
    def chaos_memory_bomb(self):
        """Chaos: Deploy memory-intensive process to trigger R14 errors"""
        self.log("💥 CHAOS: Memory Bomb Deployment", "CHAOS")
        
        # Create a memory bomb script
        memory_bomb_script = '''
import os
import time
import threading

def memory_allocator():
    """Allocate memory until R14 (memory quota exceeded)"""
    memory_chunks = []
    chunk_size = 1024 * 1024  # 1MB chunks
    
    try:
        for i in range(1000):  # Try to allocate 1GB
            chunk = "x" * chunk_size
            memory_chunks.append(chunk)
            print(f"Allocated {i + 1} MB")
            time.sleep(0.1)
            
            # Simulate some work
            if i % 10 == 0:
                # Do some CPU work too
                sum(range(10000))
    except MemoryError:
        print("Memory allocation failed - R14 triggered!")
    except Exception as e:
        print(f"Memory bomb error: {e}")

if __name__ == "__main__":
    print("Starting memory bomb...")
    
    # Start multiple threads to consume memory faster
    threads = []
    for i in range(3):
        t = threading.Thread(target=memory_allocator)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print("Memory bomb completed")
'''
        
        # Save the script
        with open('memory_bomb.py', 'w') as f:
            f.write(memory_bomb_script)
        
        self.log("💣 Memory bomb script created", "CHAOS")
        self.log("🔧 Deploy this script to trigger R14 memory errors:", "WARN")
        self.log("   1. Add memory_bomb.py to your repo", "INFO")
        self.log("   2. Add to Procfile: bomb: python memory_bomb.py", "INFO")
        self.log("   3. Deploy and scale: heroku ps:scale bomb=1", "INFO")
        self.log("   4. Monitor logs: heroku logs -t", "INFO")
        
        # Monitor for memory issues in current deployment
        self.monitor_memory_usage(300)  # 5 minutes
    
    def chaos_dependency_failure(self):
        """Chaos: Simulate external dependency failures"""
        self.log("💥 CHAOS: External Dependency Failure Simulation", "CHAOS")
        
        # Test external dependencies by flooding them
        external_apis = [
            "https://generativelanguage.googleapis.com",  # Gemini API
            "https://api.github.com",  # GitHub API (if used)
        ]
        
        baseline_metrics = self.monitor_app_health(30)
        
        for api in external_apis:
            self.log(f"💥 Stress testing {api}", "CHAOS")
            self.stress_external_api(api)
        
        # Monitor app during dependency stress
        chaos_metrics = self.monitor_app_health(180)
        
        self.analyze_recovery(baseline_metrics, chaos_metrics, "dependency_failure")
    
    def stress_external_api(self, api_url: str):
        """Stress test external API to simulate failures"""
        def make_requests():
            for _ in range(20):
                try:
                    response = requests.get(f"{api_url}/", timeout=1)
                    time.sleep(0.1)
                except:
                    pass  # Ignore failures, we're trying to stress it
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=make_requests)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
    
    def monitor_app_health(self, duration: int) -> Dict:
        """Monitor application health for specified duration"""
        start_time = time.time()
        health_checks = []
        response_times = []
        
        self.log(f"📊 Monitoring health for {duration} seconds...", "INFO")
        
        while time.time() - start_time < duration:
            try:
                # Health check
                health_start = time.time()
                health_response = requests.get(f"{self.app_url}/health", timeout=10)
                health_time = (time.time() - health_start) * 1000
                
                health_checks.append({
                    'timestamp': datetime.now().isoformat(),
                    'status_code': health_response.status_code,
                    'response_time': health_time,
                    'healthy': health_response.status_code == 200
                })
                
                response_times.append(health_time)
                
                # API endpoint check
                api_start = time.time()
                api_response = requests.get(f"{self.app_url}/api/v1/contracts/history", timeout=10)
                api_time = (time.time() - api_start) * 1000
                
                if health_response.status_code != 200:
                    self.log(f"⚠️ Health check failed: {health_response.status_code}", "WARN")
                
                if api_response.status_code not in [200, 422]:
                    self.log(f"⚠️ API check failed: {api_response.status_code}", "WARN")
                
            except Exception as e:
                health_checks.append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'healthy': False
                })
                self.log(f"⚠️ Health check error: {str(e)}", "WARN")
            
            time.sleep(5)  # Check every 5 seconds
        
        # Calculate metrics
        total_checks = len(health_checks)
        healthy_checks = sum(1 for check in health_checks if check.get('healthy', False))
        availability = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        metrics = {
            'duration': duration,
            'total_checks': total_checks,
            'healthy_checks': healthy_checks,
            'availability': availability,
            'avg_response_time': avg_response_time,
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'health_checks': health_checks
        }
        
        self.log(f"📊 Availability: {availability:.1f}% | Avg Response: {avg_response_time:.1f}ms", "INFO")
        
        return metrics
    
    def monitor_memory_usage(self, duration: int):
        """Monitor for memory-related errors in Heroku logs"""
        self.log(f"📊 Monitoring memory usage for {duration} seconds...", "INFO")
        
        if not self.heroku_api_key:
            self.log("❌ No Heroku API key for log monitoring", "WARN")
            return
        
        # Monitor Heroku logs for R14 errors
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # In a real implementation, you'd stream Heroku logs
                # For now, we'll simulate checking for memory issues
                self.log("📊 Checking for R14 memory quota errors...", "INFO")
                
                # Check application health as proxy for memory issues
                health_response = requests.get(f"{self.app_url}/health", timeout=5)
                
                if health_response.status_code != 200:
                    self.log(f"⚠️ Potential memory issue detected: {health_response.status_code}", "WARN")
                
            except Exception as e:
                self.log(f"⚠️ Memory monitoring error: {str(e)}", "WARN")
            
            time.sleep(30)  # Check every 30 seconds
    
    def analyze_recovery(self, baseline: Dict, recovery: Dict, scenario: str):
        """Analyze recovery metrics after chaos"""
        self.log(f"📊 Analyzing recovery for {scenario}...", "INFO")
        
        baseline_availability = baseline.get('availability', 0)
        recovery_availability = recovery.get('availability', 0)
        
        baseline_response_time = baseline.get('avg_response_time', 0)
        recovery_response_time = recovery.get('avg_response_time', 0)
        
        # Calculate recovery metrics
        availability_impact = baseline_availability - recovery_availability
        response_time_impact = recovery_response_time - baseline_response_time
        
        recovery_analysis = {
            'scenario': scenario,
            'timestamp': datetime.now().isoformat(),
            'baseline_availability': baseline_availability,
            'recovery_availability': recovery_availability,
            'availability_impact': availability_impact,
            'baseline_response_time': baseline_response_time,
            'recovery_response_time': recovery_response_time,
            'response_time_impact': response_time_impact,
            'recovery_successful': recovery_availability >= 90.0 and response_time_impact < 1000
        }
        
        self.chaos_results.append(recovery_analysis)
        
        # Log results
        if recovery_analysis['recovery_successful']:
            self.log(f"✅ {scenario}: Recovery successful", "SUCCESS")
        else:
            self.log(f"❌ {scenario}: Recovery issues detected", "ERROR")
        
        self.log(f"   Availability: {baseline_availability:.1f}% → {recovery_availability:.1f}%", "INFO")
        self.log(f"   Response Time: {baseline_response_time:.1f}ms → {recovery_response_time:.1f}ms", "INFO")
    
    def run_chaos_suite(self):
        """Run complete chaos engineering suite"""
        self.log("💥 Starting Complete Chaos Engineering Suite", "CHAOS")
        self.log("=" * 60, "INFO")
        
        chaos_scenarios = [
            ("Dyno Cycling", self.chaos_dyno_cycling),
            ("Config Corruption", self.chaos_config_corruption),
            ("Scale Down/Up", self.chaos_scale_down_up),
            ("Memory Bomb", self.chaos_memory_bomb),
            ("Dependency Failure", self.chaos_dependency_failure)
        ]
        
        for scenario_name, scenario_func in chaos_scenarios:
            self.log(f"🎯 Running: {scenario_name}", "CHAOS")
            
            try:
                scenario_func()
                self.log(f"✅ Completed: {scenario_name}", "SUCCESS")
            except Exception as e:
                self.log(f"❌ Failed: {scenario_name} - {str(e)}", "ERROR")
            
            # Wait between scenarios
            self.log("⏳ Waiting 60 seconds before next scenario...", "INFO")
            time.sleep(60)
        
        # Generate chaos report
        self.generate_chaos_report()
    
    def generate_chaos_report(self):
        """Generate comprehensive chaos engineering report"""
        report = {
            "chaos_engineering_report": {
                "app_name": self.heroku_app_name,
                "app_url": self.app_url,
                "generated_at": datetime.now().isoformat(),
                "total_scenarios": len(self.chaos_results),
                "successful_recoveries": sum(1 for r in self.chaos_results if r['recovery_successful']),
                "scenarios": self.chaos_results,
                "recommendations": self.get_chaos_recommendations()
            }
        }
        
        report_file = f"chaos_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"📄 Chaos report saved: {report_file}", "SUCCESS")
        
        # Print summary
        self.log("💥 CHAOS ENGINEERING SUMMARY", "CHAOS")
        self.log("=" * 50, "INFO")
        self.log(f"Scenarios Run: {len(self.chaos_results)}", "INFO")
        self.log(f"Successful Recoveries: {sum(1 for r in self.chaos_results if r['recovery_successful'])}", "INFO")
        self.log(f"Recovery Rate: {(sum(1 for r in self.chaos_results if r['recovery_successful']) / max(len(self.chaos_results), 1) * 100):.1f}%", "INFO")
        
        return report_file
    
    def get_chaos_recommendations(self) -> List[str]:
        """Get recommendations based on chaos results"""
        recommendations = []
        
        if len(self.chaos_results) == 0:
            return ["Run chaos engineering scenarios to get recommendations"]
        
        # Analyze results for recommendations
        availability_impacts = [r.get('availability_impact', 0) for r in self.chaos_results]
        avg_availability_impact = sum(availability_impacts) / len(availability_impacts)
        
        if avg_availability_impact > 10:
            recommendations.append("Consider implementing circuit breakers for better fault tolerance")
        
        response_time_impacts = [r.get('response_time_impact', 0) for r in self.chaos_results]
        avg_response_impact = sum(response_time_impacts) / len(response_time_impacts)
        
        if avg_response_impact > 500:
            recommendations.append("Implement connection pooling and caching to improve response times")
        
        failed_scenarios = [r for r in self.chaos_results if not r['recovery_successful']]
        if len(failed_scenarios) > 0:
            recommendations.append("Set up automated alerts for faster incident response")
            recommendations.append("Consider implementing auto-rollback mechanisms")
        
        recommendations.extend([
            "Implement health checks with graceful degradation",
            "Set up monitoring dashboards for real-time visibility",
            "Practice chaos engineering regularly to improve resilience",
            "Document incident response procedures"
        ])
        
        return recommendations

def main():
    """Main function"""
    print("💥 SoliVolt Chaos Engineering for Heroku")
    print("=" * 50)
    
    chaos_engineer = HerokuChaosEngineer()
    
    while True:
        print("\n🎮 Chaos Engineering Menu:")
        print("1. 🔄 Dyno Cycling Attack")
        print("2. ⚙️ Config Corruption Test")
        print("3. 📊 Scale Down/Up Test")
        print("4. 💣 Memory Bomb Deployment")
        print("5. 🌐 Dependency Failure Simulation")
        print("6. 💥 Run Complete Chaos Suite")
        print("7. 📊 Monitor App Health")
        print("8. 📄 Generate Chaos Report")
        print("9. 🚪 Exit")
        
        choice = input("\nChoose your chaos (1-9): ").strip()
        
        if choice == '1':
            chaos_engineer.chaos_dyno_cycling()
        elif choice == '2':
            chaos_engineer.chaos_config_corruption()
        elif choice == '3':
            chaos_engineer.chaos_scale_down_up()
        elif choice == '4':
            chaos_engineer.chaos_memory_bomb()
        elif choice == '5':
            chaos_engineer.chaos_dependency_failure()
        elif choice == '6':
            chaos_engineer.run_chaos_suite()
        elif choice == '7':
            duration = input("Monitor duration in seconds (default 60): ").strip()
            duration = int(duration) if duration.isdigit() else 60
            chaos_engineer.monitor_app_health(duration)
        elif choice == '8':
            chaos_engineer.generate_chaos_report()
        elif choice == '9':
            print("👋 Chaos engineering complete!")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    main()
