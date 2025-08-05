#!/usr/bin/env python3
"""
🔥 SoliVolt Chaos Engineering Suite
Implements chaos engineering tests to validate system resilience
"""

import os
import sys
import time
import random
import subprocess
import requests
import threading
from datetime import datetime
from typing import Dict, List, Any

class ChaosEngineer:
    """
    Chaos Engineering implementation for SoliVolt
    Tests system resilience through controlled failure injection
    """
    
    def __init__(self):
        self.target_url = os.getenv('TARGET_URL', 'http://localhost:8000')
        self.results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and color coding"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        colors = {
            "INFO": "\033[32m",    # Green
            "WARN": "\033[33m",    # Yellow  
            "ERROR": "\033[31m",   # Red
            "CHAOS": "\033[35m",   # Magenta
            "RESET": "\033[0m"     # Reset
        }
        color = colors.get(level, colors["INFO"])
        print(f"{color}[{timestamp}] [CHAOS-{level}] {message}{colors['RESET']}")

    def baseline_test(self):
        """Establish baseline system performance"""
        self.log("📊 Establishing baseline performance...", "INFO")
        
        baseline = {
            'response_times': [],
            'success_rate': 0,
            'error_count': 0,
            'total_requests': 100
        }
        
        successful_requests = 0
        
        for i in range(baseline['total_requests']):
            try:
                start_time = time.time()
                response = requests.get(f"{self.target_url}/health", timeout=5)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                baseline['response_times'].append(response_time)
                
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    baseline['error_count'] += 1
                    
            except Exception as e:
                baseline['error_count'] += 1
                baseline['response_times'].append(5000)  # Timeout = 5000ms
                
        baseline['success_rate'] = (successful_requests / baseline['total_requests']) * 100
        baseline['avg_response_time'] = sum(baseline['response_times']) / len(baseline['response_times'])
        
        self.log(f"✅ Baseline established:", "INFO")
        self.log(f"   Success Rate: {baseline['success_rate']:.1f}%")
        self.log(f"   Avg Response Time: {baseline['avg_response_time']:.1f}ms")
        self.log(f"   Error Count: {baseline['error_count']}")
        
        return baseline

    def chaos_test_database_failure(self):
        """Test system behavior when database fails"""
        self.log("🗄️ CHAOS TEST: Database Connection Failure", "CHAOS")
        
        try:
            # Stop database container
            self.log("Stopping database container...", "WARN")
            result = subprocess.run(['docker', 'stop', 'smart_contract_db'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log("✅ Database stopped successfully")
                
                # Test system behavior
                failure_metrics = self.test_system_during_failure("database_failure")
                
                # Restart database
                self.log("🔄 Restarting database...", "INFO")
                subprocess.run(['docker', 'start', 'smart_contract_db'], 
                             capture_output=True, text=True, timeout=30)
                
                # Wait for database to be ready
                self.log("⏳ Waiting for database to be ready...")
                time.sleep(15)
                
                # Test recovery
                recovery_metrics = self.test_system_recovery("database_recovery")
                
                return {
                    'test': 'database_failure',
                    'failure_metrics': failure_metrics,
                    'recovery_metrics': recovery_metrics,
                    'status': 'completed'
                }
            else:
                self.log(f"❌ Failed to stop database: {result.stderr}", "ERROR")
                return {'test': 'database_failure', 'status': 'failed', 'error': result.stderr}
                
        except Exception as e:
            self.log(f"❌ Database chaos test failed: {str(e)}", "ERROR")
            return {'test': 'database_failure', 'status': 'error', 'exception': str(e)}

    def chaos_test_memory_stress(self):
        """Test system behavior under memory pressure"""
        self.log("💾 CHAOS TEST: Memory Stress", "CHAOS")
        
        # Create memory stress script
        stress_script = f"""
import time
import threading

def memory_stress():
    memory_hog = []
    try:
        for i in range(1000):
            # Allocate 1MB chunks
            memory_hog.append('x' * 1024 * 1024)
            time.sleep(0.01)
    except MemoryError:
        pass

# Start multiple threads
threads = []
for i in range(4):
    t = threading.Thread(target=memory_stress)
    threads.append(t)
    t.start()

time.sleep(30)  # Run for 30 seconds

for t in threads:
    t.join()
"""
        
        stress_file = 'memory_stress.py'
        with open(stress_file, 'w') as f:
            f.write(stress_script)
            
        try:
            self.log("🔥 Starting memory stress test...", "WARN")
            
            # Start stress test in background
            stress_process = subprocess.Popen([sys.executable, stress_file])
            
            # Monitor system during stress
            failure_metrics = self.test_system_during_failure("memory_stress")
            
            # Wait for stress test to complete
            stress_process.wait()
            
            # Test recovery
            recovery_metrics = self.test_system_recovery("memory_recovery")
            
            return {
                'test': 'memory_stress',
                'failure_metrics': failure_metrics,
                'recovery_metrics': recovery_metrics,
                'status': 'completed'
            }
            
        except Exception as e:
            self.log(f"❌ Memory stress test failed: {str(e)}", "ERROR")
            return {'test': 'memory_stress', 'status': 'error', 'exception': str(e)}
        finally:
            # Cleanup
            if os.path.exists(stress_file):
                os.remove(stress_file)

    def chaos_test_network_partition(self):
        """Simulate network partition using iptables"""
        self.log("🌐 CHAOS TEST: Network Partition", "CHAOS")
        
        try:
            # Block traffic to external services (simulate partition)
            self.log("🚫 Creating network partition...", "WARN")
            
            # Block DNS (simulate network issues)
            block_cmd = ['sudo', 'iptables', '-A', 'OUTPUT', '-p', 'udp', '--dport', '53', '-j', 'DROP']
            subprocess.run(block_cmd, capture_output=True, text=True)
            
            # Test system behavior
            failure_metrics = self.test_system_during_failure("network_partition")
            
            # Restore network
            self.log("🔄 Restoring network...", "INFO")
            restore_cmd = ['sudo', 'iptables', '-D', 'OUTPUT', '-p', 'udp', '--dport', '53', '-j', 'DROP']
            subprocess.run(restore_cmd, capture_output=True, text=True)
            
            # Test recovery
            recovery_metrics = self.test_system_recovery("network_recovery")
            
            return {
                'test': 'network_partition',
                'failure_metrics': failure_metrics,
                'recovery_metrics': recovery_metrics,
                'status': 'completed'
            }
            
        except Exception as e:
            self.log(f"❌ Network partition test failed: {str(e)}", "ERROR")
            # Attempt to restore network
            try:
                restore_cmd = ['sudo', 'iptables', '-D', 'OUTPUT', '-p', 'udp', '--dport', '53', '-j', 'DROP']
                subprocess.run(restore_cmd, capture_output=True, text=True)
            except:
                pass
            return {'test': 'network_partition', 'status': 'error', 'exception': str(e)}

    def chaos_test_cpu_stress(self):
        """Test system behavior under CPU stress"""
        self.log("⚡ CHAOS TEST: CPU Stress", "CHAOS")
        
        # Create CPU stress script
        stress_script = f"""
import time
import threading
import multiprocessing

def cpu_stress():
    end_time = time.time() + 20  # Run for 20 seconds
    while time.time() < end_time:
        # Busy loop to consume CPU
        for _ in range(10000):
            pass

# Create threads equal to CPU count
cpu_count = multiprocessing.cpu_count()
threads = []

for i in range(cpu_count * 2):  # Oversubscribe CPU
    t = threading.Thread(target=cpu_stress)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
"""
        
        stress_file = 'cpu_stress.py'
        with open(stress_file, 'w') as f:
            f.write(stress_script)
            
        try:
            self.log("🔥 Starting CPU stress test...", "WARN")
            
            # Start stress test
            stress_process = subprocess.Popen([sys.executable, stress_file])
            
            # Monitor system during stress
            failure_metrics = self.test_system_during_failure("cpu_stress")
            
            # Wait for stress test to complete
            stress_process.wait()
            
            # Test recovery
            recovery_metrics = self.test_system_recovery("cpu_recovery")
            
            return {
                'test': 'cpu_stress',
                'failure_metrics': failure_metrics,
                'recovery_metrics': recovery_metrics,
                'status': 'completed'
            }
            
        except Exception as e:
            self.log(f"❌ CPU stress test failed: {str(e)}", "ERROR")
            return {'test': 'cpu_stress', 'status': 'error', 'exception': str(e)}
        finally:
            if os.path.exists(stress_file):
                os.remove(stress_file)

    def chaos_test_environment_corruption(self):
        """Test system behavior when environment variables are corrupted"""
        self.log("🔧 CHAOS TEST: Environment Variable Corruption", "CHAOS")
        
        env_file = 'backend/.env'
        backup_file = 'backend/.env.chaos_backup'
        
        try:
            # Backup current .env
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    backup_content = f.read()
                with open(backup_file, 'w') as f:
                    f.write(backup_content)
                
                self.log("💾 Backed up current environment", "INFO")
                
                # Corrupt critical environment variables
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Remove GEMINI_API_KEY and DATABASE_URL
                corrupted_content = content.replace('GEMINI_API_KEY=', '#GEMINI_API_KEY=')
                corrupted_content = corrupted_content.replace('DATABASE_URL=', '#DATABASE_URL=')
                
                with open(env_file, 'w') as f:
                    f.write(corrupted_content)
                
                self.log("💥 Corrupted environment variables", "WARN")
                
                # Restart backend to pick up changes
                self.log("🔄 Restarting backend service...", "INFO")
                subprocess.run(['docker-compose', 'restart', 'backend'], capture_output=True)
                time.sleep(10)
                
                # Test system behavior
                failure_metrics = self.test_system_during_failure("env_corruption")
                
                # Restore environment
                self.log("🔄 Restoring environment...", "INFO")
                with open(backup_file, 'r') as f:
                    original_content = f.read()
                with open(env_file, 'w') as f:
                    f.write(original_content)
                
                # Restart backend again
                subprocess.run(['docker-compose', 'restart', 'backend'], capture_output=True)
                time.sleep(10)
                
                # Test recovery
                recovery_metrics = self.test_system_recovery("env_recovery")
                
                return {
                    'test': 'environment_corruption',
                    'failure_metrics': failure_metrics,
                    'recovery_metrics': recovery_metrics,
                    'status': 'completed'
                }
            else:
                self.log("❌ .env file not found", "ERROR")
                return {'test': 'environment_corruption', 'status': 'failed', 'error': '.env file not found'}
                
        except Exception as e:
            self.log(f"❌ Environment corruption test failed: {str(e)}", "ERROR")
            return {'test': 'environment_corruption', 'status': 'error', 'exception': str(e)}
        finally:
            # Cleanup backup
            if os.path.exists(backup_file):
                os.remove(backup_file)

    def test_system_during_failure(self, test_name: str) -> Dict:
        """Test system behavior during failure injection"""
        self.log(f"🧪 Testing system behavior during {test_name}...", "INFO")
        
        metrics = {
            'test_name': test_name,
            'requests_sent': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'response_times': [],
            'error_types': {},
            'start_time': time.time()
        }
        
        # Test different endpoints
        endpoints = [
            '/health',
            '/api/v1/contracts/history',
            '/docs'
        ]
        
        # Run tests for 30 seconds
        end_time = time.time() + 30
        
        while time.time() < end_time:
            for endpoint in endpoints:
                try:
                    start = time.time()
                    response = requests.get(f"{self.target_url}{endpoint}", timeout=5)
                    end = time.time()
                    
                    metrics['requests_sent'] += 1
                    metrics['response_times'].append((end - start) * 1000)
                    
                    if response.status_code == 200:
                        metrics['requests_successful'] += 1
                    else:
                        metrics['requests_failed'] += 1
                        error_type = f"HTTP_{response.status_code}"
                        metrics['error_types'][error_type] = metrics['error_types'].get(error_type, 0) + 1
                        
                except requests.exceptions.RequestException as e:
                    metrics['requests_sent'] += 1
                    metrics['requests_failed'] += 1
                    metrics['response_times'].append(5000)  # Timeout
                    
                    error_type = type(e).__name__
                    metrics['error_types'][error_type] = metrics['error_types'].get(error_type, 0) + 1
                    
                time.sleep(0.5)  # Prevent overwhelming the system
        
        metrics['end_time'] = time.time()
        metrics['duration'] = metrics['end_time'] - metrics['start_time']
        metrics['success_rate'] = (metrics['requests_successful'] / max(metrics['requests_sent'], 1)) * 100
        
        if metrics['response_times']:
            metrics['avg_response_time'] = sum(metrics['response_times']) / len(metrics['response_times'])
        else:
            metrics['avg_response_time'] = 0
        
        self.log(f"📊 Failure test results:", "INFO")
        self.log(f"   Requests: {metrics['requests_sent']}")
        self.log(f"   Success Rate: {metrics['success_rate']:.1f}%")
        self.log(f"   Avg Response Time: {metrics['avg_response_time']:.1f}ms")
        self.log(f"   Errors: {metrics['error_types']}")
        
        return metrics

    def test_system_recovery(self, test_name: str) -> Dict:
        """Test system recovery after failure injection"""
        self.log(f"🔄 Testing system recovery for {test_name}...", "INFO")
        
        # Wait a bit for system to stabilize
        time.sleep(5)
        
        recovery_metrics = {
            'test_name': test_name,
            'recovery_time': 0,
            'final_success_rate': 0,
            'final_response_time': 0
        }
        
        # Test recovery over 60 seconds
        recovery_start = time.time()
        consecutive_successes = 0
        required_successes = 10  # Need 10 consecutive successes to consider recovered
        
        while time.time() - recovery_start < 60:
            try:
                start = time.time()
                response = requests.get(f"{self.target_url}/health", timeout=5)
                end = time.time()
                
                if response.status_code == 200:
                    consecutive_successes += 1
                    if consecutive_successes >= required_successes:
                        recovery_metrics['recovery_time'] = time.time() - recovery_start
                        self.log(f"✅ System recovered in {recovery_metrics['recovery_time']:.1f} seconds")
                        break
                else:
                    consecutive_successes = 0
                    
            except:
                consecutive_successes = 0
                
            time.sleep(1)
        
        # Final system test
        final_metrics = self.test_system_during_failure(f"{test_name}_final")
        recovery_metrics['final_success_rate'] = final_metrics['success_rate']
        recovery_metrics['final_response_time'] = final_metrics['avg_response_time']
        
        if recovery_metrics['recovery_time'] == 0:
            recovery_metrics['recovery_time'] = 60  # Max time if not recovered
            self.log("⚠️ System did not fully recover within 60 seconds", "WARN")
        
        return recovery_metrics

    def run_chaos_suite(self):
        """Run the complete chaos engineering test suite"""
        self.log("🔥 Starting SoliVolt Chaos Engineering Suite", "CHAOS")
        self.log("=" * 80)
        
        # Establish baseline
        baseline = self.baseline_test()
        
        # Chaos tests to run
        chaos_tests = [
            self.chaos_test_database_failure,
            self.chaos_test_memory_stress,
            self.chaos_test_cpu_stress,
            self.chaos_test_environment_corruption,
            # self.chaos_test_network_partition,  # Requires sudo, commented out
        ]
        
        results = {
            'baseline': baseline,
            'tests': [],
            'summary': {}
        }
        
        for test_func in chaos_tests:
            self.log(f"\n{'='*50}", "CHAOS")
            try:
                test_result = test_func()
                results['tests'].append(test_result)
                self.results.append(test_result)
                
                # Wait between tests for system to stabilize
                self.log("⏳ Waiting for system to stabilize...", "INFO")
                time.sleep(10)
                
            except Exception as e:
                self.log(f"❌ Test failed with exception: {str(e)}", "ERROR")
                results['tests'].append({
                    'test': test_func.__name__,
                    'status': 'exception',
                    'error': str(e)
                })
        
        # Generate summary
        total_tests = len(results['tests'])
        successful_tests = len([t for t in results['tests'] if t.get('status') == 'completed'])
        
        results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': (successful_tests / max(total_tests, 1)) * 100,
            'baseline_success_rate': baseline['success_rate'],
            'baseline_response_time': baseline['avg_response_time']
        }
        
        self.log("\n🎯 CHAOS ENGINEERING SUMMARY", "CHAOS")
        self.log("=" * 80)
        self.log(f"📊 Tests Run: {total_tests}")
        self.log(f"✅ Successful: {successful_tests}")
        self.log(f"📈 Test Success Rate: {results['summary']['success_rate']:.1f}%")
        self.log(f"🎯 Baseline Success Rate: {baseline['success_rate']:.1f}%")
        self.log(f"⚡ Baseline Response Time: {baseline['avg_response_time']:.1f}ms")
        
        # Save results
        import json
        report_file = f"chaos_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.log(f"📝 Detailed report saved to {report_file}")
        
        return results

def main():
    """Main execution function"""
    print("🔥 SoliVolt Chaos Engineering Suite")
    print("====================================")
    print("Testing system resilience through controlled failure injection\n")
    
    chaos_engineer = ChaosEngineer()
    
    while True:
        print("\n🧪 Choose a chaos test:")
        print("1. Run Full Chaos Suite")
        print("2. Database Failure Test")
        print("3. Memory Stress Test") 
        print("4. CPU Stress Test")
        print("5. Environment Corruption Test")
        print("6. Baseline Performance Test")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            chaos_engineer.run_chaos_suite()
        elif choice == '2':
            result = chaos_engineer.chaos_test_database_failure()
            print(f"Result: {result}")
        elif choice == '3':
            result = chaos_engineer.chaos_test_memory_stress()
            print(f"Result: {result}")
        elif choice == '4':
            result = chaos_engineer.chaos_test_cpu_stress()
            print(f"Result: {result}")
        elif choice == '5':
            result = chaos_engineer.chaos_test_environment_corruption()
            print(f"Result: {result}")
        elif choice == '6':
            baseline = chaos_engineer.baseline_test()
            print(f"Baseline: {baseline}")
        elif choice == '7':
            print("👋 Chaos testing complete!")
            break
        else:
            print("❌ Invalid choice, please try again.")

if __name__ == "__main__":
    main()
