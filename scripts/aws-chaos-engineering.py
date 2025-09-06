#!/usr/bin/env python3
"""
🔥 AWS EC2 Microservices Chaos Engineering
Chaos engineering tests for resilience validation
"""

import os
import sys
import time
import random
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Any

class MicroservicesChaosEngineer:
    """
    Chaos Engineering for AWS EC2 Microservices
    Tests system resilience through controlled failure injection
    """
    
    def __init__(self):
        self.ec2_host = os.getenv('EC2_HOST', 'localhost')
        self.services = {
            'unified_main': {
                'port': 8000,
                'container': 'microservices-unified-main-1',
                'health_endpoint': '/health'
            },
            'contract_service': {
                'port': 8001,
                'container': 'microservices-contract-service-1',
                'health_endpoint': '/health'
            },
            'postgres': {
                'port': 5432,
                'container': 'microservices-postgres-1',
                'health_endpoint': None
            }
        }
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
        reset = colors["RESET"]
        print(f"{color}[{timestamp}] {level}: {message}{reset}")
    
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        service = self.services.get(service_name)
        if not service or not service.get('health_endpoint'):
            return True  # Skip health check for services without endpoints
        
        url = f"http://{self.ec2_host}:{service['port']}{service['health_endpoint']}"
        
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_recovery(self, service_name: str, max_wait: int = 60) -> bool:
        """Wait for service to recover"""
        self.log(f"⏳ Waiting for {service_name} to recover...", "INFO")
        
        for i in range(max_wait):
            if self.check_service_health(service_name):
                self.log(f"✅ {service_name} recovered after {i+1} seconds", "INFO")
                return True
            time.sleep(1)
        
        self.log(f"❌ {service_name} failed to recover within {max_wait} seconds", "ERROR")
        return False
    
    def container_kill_test(self, service_name: str) -> Dict[str, Any]:
        """Kill a container and test recovery"""
        self.log(f"🔥 CHAOS: Killing {service_name} container", "CHAOS")
        
        container = self.services[service_name]['container']
        start_time = time.time()
        
        try:
            # Kill the container
            subprocess.run(['docker', 'kill', container], check=True, capture_output=True)
            self.log(f"💀 Container {container} killed", "WARN")
            
            # Wait a moment for Docker Compose to restart it
            time.sleep(5)
            
            # Check recovery
            recovered = self.wait_for_recovery(service_name, max_wait=60)
            recovery_time = time.time() - start_time
            
            return {
                'test': 'container_kill',
                'service': service_name,
                'success': recovered,
                'recovery_time': recovery_time,
                'details': f'Container killed and {"recovered" if recovered else "failed to recover"}'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'test': 'container_kill',
                'service': service_name,
                'success': False,
                'error': str(e),
                'details': 'Failed to kill container'
            }
    
    def service_overload_test(self, service_name: str, duration: int = 30) -> Dict[str, Any]:
        """Overload a service with requests"""
        service = self.services.get(service_name)
        if not service or not service.get('health_endpoint'):
            return {
                'test': 'service_overload',
                'service': service_name,
                'success': False,
                'details': 'Service not suitable for overload testing'
            }
        
        self.log(f"🌪️ CHAOS: Overloading {service_name} for {duration} seconds", "CHAOS")
        
        url = f"http://{self.ec2_host}:{service['port']}{service['health_endpoint']}"
        start_time = time.time()
        
        # Check initial health
        initial_health = self.check_service_health(service_name)
        if not initial_health:
            return {
                'test': 'service_overload',
                'service': service_name,
                'success': False,
                'details': 'Service was unhealthy before test'
            }
        
        # Start overload
        successful_requests = 0
        failed_requests = 0
        
        end_time = start_time + duration
        while time.time() < end_time:
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
            except:
                failed_requests += 1
        
        # Check final health
        time.sleep(5)  # Let service stabilize
        final_health = self.check_service_health(service_name)
        
        total_requests = successful_requests + failed_requests
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'test': 'service_overload',
            'service': service_name,
            'success': final_health,
            'total_requests': total_requests,
            'error_rate': error_rate,
            'details': f'Sent {total_requests} requests, {error_rate:.1f}% error rate'
        }
    
    def network_partition_test(self, duration: int = 15) -> Dict[str, Any]:
        """Simulate network partition by blocking traffic"""
        self.log(f"🌐 CHAOS: Simulating network partition for {duration} seconds", "CHAOS")
        
        try:
            # Block traffic to services (simplified - blocks all traffic on service ports)
            for service in self.services.values():
                if service.get('port') != 5432:  # Don't block postgres
                    subprocess.run([
                        'sudo', 'iptables', '-A', 'INPUT', '-p', 'tcp', 
                        '--dport', str(service['port']), '-j', 'DROP'
                    ], capture_output=True)
            
            self.log(f"🚫 Network partition active", "WARN")
            time.sleep(duration)
            
            # Restore network
            for service in self.services.values():
                if service.get('port') != 5432:
                    subprocess.run([
                        'sudo', 'iptables', '-D', 'INPUT', '-p', 'tcp',
                        '--dport', str(service['port']), '-j', 'DROP'
                    ], capture_output=True)
            
            self.log(f"🔄 Network partition ended", "INFO")
            
            # Check service recovery
            time.sleep(10)
            all_healthy = all(self.check_service_health(svc) for svc in ['unified_main', 'contract_service'])
            
            return {
                'test': 'network_partition',
                'service': 'all',
                'success': all_healthy,
                'duration': duration,
                'details': f'Network partition for {duration}s, services {"recovered" if all_healthy else "failed to recover"}'
            }
            
        except Exception as e:
            return {
                'test': 'network_partition',
                'service': 'all',
                'success': False,
                'error': str(e),
                'details': 'Failed to execute network partition test'
            }
    
    def memory_stress_test(self, service_name: str, duration: int = 30) -> Dict[str, Any]:
        """Stress test service memory"""
        self.log(f"🧠 CHAOS: Memory stress test on {service_name} for {duration} seconds", "CHAOS")
        
        container = self.services[service_name]['container']
        
        try:
            # Run memory stress inside container
            stress_cmd = [
                'docker', 'exec', container,
                'python', '-c', 
                f'import time; x=[" "*1024*1024 for i in range(100)]; time.sleep({duration})'
            ]
            
            # Start stress test in background
            process = subprocess.Popen(stress_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Monitor service health during stress
            healthy_checks = 0
            total_checks = 0
            
            for _ in range(duration):
                if self.check_service_health(service_name):
                    healthy_checks += 1
                total_checks += 1
                time.sleep(1)
            
            # Stop stress test
            process.terminate()
            process.wait(timeout=5)
            
            # Final health check
            time.sleep(5)
            final_health = self.check_service_health(service_name)
            
            uptime_percentage = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            
            return {
                'test': 'memory_stress',
                'service': service_name,
                'success': final_health and uptime_percentage >= 80,  # 80% uptime threshold
                'uptime_percentage': uptime_percentage,
                'details': f'Service maintained {uptime_percentage:.1f}% uptime during memory stress'
            }
            
        except Exception as e:
            return {
                'test': 'memory_stress',
                'service': service_name,
                'success': False,
                'error': str(e),
                'details': 'Failed to execute memory stress test'
            }
    
    def run_chaos_suite(self) -> List[Dict[str, Any]]:
        """Run complete chaos engineering suite"""
        self.log("🚀 Starting Chaos Engineering Suite", "CHAOS")
        
        tests = [
            # Container resilience tests
            lambda: self.container_kill_test('unified_main'),
            lambda: self.container_kill_test('contract_service'),
            
            # Service overload tests
            lambda: self.service_overload_test('unified_main', 20),
            lambda: self.service_overload_test('contract_service', 20),
            
            # Memory stress tests
            lambda: self.memory_stress_test('unified_main', 15),
            lambda: self.memory_stress_test('contract_service', 15),
        ]
        
        results = []
        
        for i, test in enumerate(tests, 1):
            self.log(f"🧪 Running test {i}/{len(tests)}", "INFO")
            
            try:
                result = test()
                results.append(result)
                
                # Log result
                status = "✅ PASSED" if result['success'] else "❌ FAILED"
                self.log(f"{status}: {result['test']} on {result['service']}", "INFO")
                
                # Wait between tests
                if i < len(tests):
                    self.log("⏸️ Waiting 10 seconds before next test...", "INFO")
                    time.sleep(10)
                    
            except Exception as e:
                self.log(f"💥 Test {i} crashed: {e}", "ERROR")
                results.append({
                    'test': f'test_{i}',
                    'service': 'unknown',
                    'success': False,
                    'error': str(e)
                })
        
        self.results = results
        return results
    
    def generate_report(self) -> str:
        """Generate chaos engineering report"""
        if not self.results:
            return "No chaos engineering results available"
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        report = []
        report.append("🔥 CHAOS ENGINEERING REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        report.append(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        report.append("")
        
        # Individual test results
        report.append("📋 TEST RESULTS:")
        for i, result in enumerate(self.results, 1):
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            test_name = result['test'].replace('_', ' ').title()
            service = result['service']
            
            report.append(f"{i}. {status} - {test_name} ({service})")
            if 'details' in result:
                report.append(f"   📝 {result['details']}")
            if 'error' in result:
                report.append(f"   ⚠️  Error: {result['error']}")
            report.append("")
        
        # Recommendations
        if failed_tests > 0:
            report.append("🔧 RECOMMENDATIONS:")
            report.append("- Review failed tests and improve service resilience")
            report.append("- Consider implementing circuit breakers")
            report.append("- Add more monitoring and alerting")
            report.append("- Implement graceful degradation patterns")
        else:
            report.append("🎉 EXCELLENT RESILIENCE!")
            report.append("All chaos tests passed. Your microservices are resilient!")
        
        return "\n".join(report)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AWS EC2 Microservices Chaos Engineering")
    parser.add_argument('--host', default='localhost', help='EC2 host IP')
    parser.add_argument('--test', choices=['kill', 'overload', 'network', 'memory', 'all'], 
                       default='all', help='Specific test to run')
    parser.add_argument('--service', choices=['unified_main', 'contract_service'], 
                       help='Specific service to test')
    parser.add_argument('--report', action='store_true', help='Generate report only')
    
    args = parser.parse_args()
    
    chaos = MicroservicesChaosEngineer()
    if args.host != 'localhost':
        chaos.ec2_host = args.host
    
    if args.report:
        print(chaos.generate_report())
        return
    
    # Run specific test or full suite
    if args.test == 'all':
        results = chaos.run_chaos_suite()
    else:
        if args.test == 'kill' and args.service:
            result = chaos.container_kill_test(args.service)
        elif args.test == 'overload' and args.service:
            result = chaos.service_overload_test(args.service)
        elif args.test == 'memory' and args.service:
            result = chaos.memory_stress_test(args.service)
        elif args.test == 'network':
            result = chaos.network_partition_test()
        else:
            print("Error: Specific tests require --service parameter (except network)")
            sys.exit(1)
        
        results = [result]
        chaos.results = results
    
    # Print summary
    print("\n" + chaos.generate_report())
    
    # Exit with error code if any tests failed
    failed = any(not r['success'] for r in results)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
