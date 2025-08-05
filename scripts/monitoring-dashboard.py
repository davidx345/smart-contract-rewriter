#!/usr/bin/env python3
"""
📊 SoliVolt Real-Time Monitoring Dashboard
Live monitoring of system health, performance, and metrics
"""

import os
import sys
import time
import json
import psutil
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess

class SoliVoltMonitor:
    """
    Real-time monitoring dashboard for SoliVolt infrastructure
    """
    
    def __init__(self):
        # Heroku-specific configuration
        self.target_url = os.getenv('TARGET_URL', 'https://solivolt-8e0565441715.herokuapp.com')
        self.heroku_app_name = os.getenv('HEROKU_APP_NAME', 'solivolt-8e0565441715')
        self.heroku_api_key = os.getenv('HEROKU_API_KEY', '')
        
        self.metrics_history = []
        self.alerts = []
        self.running = False
        
        # Heroku-optimized thresholds (Heroku has different resource limits)
        self.thresholds = {
            'cpu_percent': 70.0,      # Lower for Heroku dynos
            'memory_percent': 80.0,   # Heroku dynos have memory limits
            'disk_percent': 85.0,     # Heroku ephemeral filesystem
            'response_time_ms': 3000, # Higher threshold for free dynos
            'error_rate_percent': 5.0,
            'success_rate_percent': 95.0,
            'dyno_restart_threshold': 5  # Alert if too many restarts
        }
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[32m",    # Green
            "WARN": "\033[33m",    # Yellow  
            "ERROR": "\033[31m",   # Red
            "ALERT": "\033[35m",   # Magenta
            "RESET": "\033[0m"     # Reset
        }
        color = colors.get(level, colors["INFO"])
        return f"{color}[{timestamp}] {message}{colors['RESET']}"

    def get_system_metrics(self) -> Dict:
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'percent': memory_percent,
                    'used_gb': round(memory_used_gb, 2),
                    'total_gb': round(memory_total_gb, 2)
                },
                'disk': {
                    'percent': disk_percent,
                    'used_gb': round(disk_used_gb, 2),
                    'total_gb': round(disk_total_gb, 2)
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def get_application_metrics(self) -> Dict:
        """Collect application-specific metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'health_check': {'status': 'unknown', 'response_time': 0},
            'api_endpoints': {},
            'docker_containers': {}
        }
        
        # Health check
        try:
            start_time = time.time()
            response = requests.get(f"{self.target_url}/health", timeout=5)
            end_time = time.time()
            
            metrics['health_check'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time': round((end_time - start_time) * 1000, 2)
            }
        except Exception as e:
            metrics['health_check'] = {
                'status': 'error',
                'error': str(e),
                'response_time': 5000
            }
        
        # Test API endpoints
        endpoints = [
            '/docs',
            '/api/v1/contracts/history'
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.target_url}{endpoint}", timeout=5)
                end_time = time.time()
                
                metrics['api_endpoints'][endpoint] = {
                    'status_code': response.status_code,
                    'response_time': round((end_time - start_time) * 1000, 2),
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy'
                }
            except Exception as e:
                metrics['api_endpoints'][endpoint] = {
                    'status': 'error',
                    'error': str(e),
                    'response_time': 5000
                }
        
        # Docker container status
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        container = json.loads(line)
                        metrics['docker_containers'][container['Names']] = {
                            'status': container['Status'],
                            'image': container['Image'],
                            'ports': container.get('Ports', '')
                        }
        except Exception as e:
            metrics['docker_containers']['error'] = str(e)
        
        return metrics

    def check_alerts(self, system_metrics: Dict, app_metrics: Dict):
        """Check for alert conditions"""
        alerts = []
        timestamp = datetime.now()
        
        # System alerts
        if 'cpu' in system_metrics:
            cpu_percent = system_metrics['cpu']['percent']
            if cpu_percent > self.thresholds['cpu_percent']:
                alerts.append({
                    'timestamp': timestamp,
                    'type': 'system',
                    'severity': 'high' if cpu_percent > 90 else 'medium',
                    'metric': 'cpu_percent',
                    'value': cpu_percent,
                    'threshold': self.thresholds['cpu_percent'],
                    'message': f"High CPU usage: {cpu_percent:.1f}%"
                })
        
        if 'memory' in system_metrics:
            memory_percent = system_metrics['memory']['percent']
            if memory_percent > self.thresholds['memory_percent']:
                alerts.append({
                    'timestamp': timestamp,
                    'type': 'system',
                    'severity': 'high' if memory_percent > 95 else 'medium',
                    'metric': 'memory_percent',
                    'value': memory_percent,
                    'threshold': self.thresholds['memory_percent'],
                    'message': f"High memory usage: {memory_percent:.1f}%"
                })
        
        # Application alerts
        if 'health_check' in app_metrics:
            health = app_metrics['health_check']
            if health['status'] != 'healthy':
                alerts.append({
                    'timestamp': timestamp,
                    'type': 'application',
                    'severity': 'critical',
                    'metric': 'health_check',
                    'value': health['status'],
                    'message': f"Application health check failed: {health['status']}"
                })
            
            if health.get('response_time', 0) > self.thresholds['response_time_ms']:
                alerts.append({
                    'timestamp': timestamp,
                    'type': 'application',
                    'severity': 'medium',
                    'metric': 'response_time',
                    'value': health['response_time'],
                    'threshold': self.thresholds['response_time_ms'],
                    'message': f"Slow response time: {health['response_time']:.1f}ms"
                })
        
        # Add new alerts
        self.alerts.extend(alerts)
        
        # Keep only last 50 alerts
        self.alerts = self.alerts[-50:]
        
        return alerts

    def render_dashboard(self, system_metrics: Dict, app_metrics: Dict, alerts: List[Dict]):
        """Render the monitoring dashboard"""
        self.clear_screen()
        
        print("🚀 SoliVolt Real-Time Monitoring Dashboard")
        print("=" * 80)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 🔄 Refreshing every 5 seconds")
        print("=" * 80)
        
        # System Health Section
        print("\n💻 SYSTEM HEALTH")
        print("-" * 40)
        
        if 'cpu' in system_metrics:
            cpu = system_metrics['cpu']['percent']
            cpu_status = "🔴" if cpu > 80 else "🟡" if cpu > 60 else "🟢"
            print(f"{cpu_status} CPU:    {cpu:6.1f}% ({system_metrics['cpu']['count']} cores)")
        
        if 'memory' in system_metrics:
            mem = system_metrics['memory']
            mem_status = "🔴" if mem['percent'] > 85 else "🟡" if mem['percent'] > 70 else "🟢"
            print(f"{mem_status} Memory: {mem['percent']:6.1f}% ({mem['used_gb']:.1f}GB / {mem['total_gb']:.1f}GB)")
        
        if 'disk' in system_metrics:
            disk = system_metrics['disk']
            disk_status = "🔴" if disk['percent'] > 90 else "🟡" if disk['percent'] > 80 else "🟢"
            print(f"{disk_status} Disk:   {disk['percent']:6.1f}% ({disk['used_gb']:.1f}GB / {disk['total_gb']:.1f}GB)")
        
        # Application Health Section
        print("\n🚀 APPLICATION HEALTH")
        print("-" * 40)
        
        if 'health_check' in app_metrics:
            health = app_metrics['health_check']
            health_icon = "🟢" if health['status'] == 'healthy' else "🔴"
            print(f"{health_icon} Health Check: {health['status'].upper():<10} ({health['response_time']:.1f}ms)")
        
        if 'api_endpoints' in app_metrics:
            for endpoint, data in app_metrics['api_endpoints'].items():
                status_icon = "🟢" if data['status'] == 'healthy' else "🔴"
                print(f"{status_icon} {endpoint:<20} {data['status'].upper():<10} ({data['response_time']:.1f}ms)")
        
        # Docker Containers Section
        print("\n🐳 DOCKER CONTAINERS")
        print("-" * 40)
        
        if 'docker_containers' in app_metrics and app_metrics['docker_containers']:
            for name, info in app_metrics['docker_containers'].items():
                if name != 'error':
                    status_icon = "🟢" if 'Up' in info['status'] else "🔴"
                    print(f"{status_icon} {name:<20} {info['status']}")
        else:
            print("❌ No containers found or Docker not available")
        
        # Recent Alerts Section
        print("\n🚨 RECENT ALERTS")
        print("-" * 40)
        
        if alerts:
            # Show last 5 alerts
            recent_alerts = sorted(alerts, key=lambda x: x['timestamp'], reverse=True)[:5]
            for alert in recent_alerts:
                severity_icon = "🔴" if alert['severity'] == 'critical' else "🟡" if alert['severity'] == 'high' else "🟠"
                time_str = alert['timestamp'].strftime('%H:%M:%S')
                print(f"{severity_icon} [{time_str}] {alert['message']}")
        else:
            print("✅ No alerts")
        
        # Performance Metrics
        print("\n📊 PERFORMANCE METRICS")
        print("-" * 40)
        
        if len(self.metrics_history) > 1:
            recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
            
            # Calculate averages
            cpu_avg = sum(m.get('system', {}).get('cpu', {}).get('percent', 0) for m in recent_metrics) / len(recent_metrics)
            memory_avg = sum(m.get('system', {}).get('memory', {}).get('percent', 0) for m in recent_metrics) / len(recent_metrics)
            
            response_times = [m.get('application', {}).get('health_check', {}).get('response_time', 0) for m in recent_metrics]
            response_avg = sum(response_times) / len(response_times) if response_times else 0
            
            print(f"📈 Avg CPU (10min):      {cpu_avg:6.1f}%")
            print(f"📈 Avg Memory (10min):   {memory_avg:6.1f}%")
            print(f"📈 Avg Response (10min): {response_avg:6.1f}ms")
        
        # Instructions
        print("\n" + "=" * 80)
        print("🎮 CONTROLS: Press Ctrl+C to stop monitoring")
        print("=" * 80)

    def collect_metrics(self):
        """Collect all metrics"""
        system_metrics = self.get_system_metrics()
        app_metrics = self.get_application_metrics()
        
        # Store in history
        metric_entry = {
            'timestamp': datetime.now().isoformat(),
            'system': system_metrics,
            'application': app_metrics
        }
        
        self.metrics_history.append(metric_entry)
        
        # Keep only last 100 entries (for performance)
        self.metrics_history = self.metrics_history[-100:]
        
        return system_metrics, app_metrics

    def start_monitoring(self):
        """Start the monitoring dashboard"""
        print("🚀 Starting SoliVolt Monitoring Dashboard...")
        print("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                # Collect metrics
                system_metrics, app_metrics = self.collect_metrics()
                
                # Check for alerts
                new_alerts = self.check_alerts(system_metrics, app_metrics)
                
                # Render dashboard
                self.render_dashboard(system_metrics, app_metrics, new_alerts)
                
                # Wait before next update
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.running = False
            print("\n\n👋 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {str(e)}")
        finally:
            self.save_metrics_report()

    def save_metrics_report(self):
        """Save metrics to a report file"""
        if self.metrics_history:
            report_file = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report_data = {
                'summary': {
                    'start_time': self.metrics_history[0]['timestamp'],
                    'end_time': self.metrics_history[-1]['timestamp'],
                    'total_samples': len(self.metrics_history),
                    'total_alerts': len(self.alerts)
                },
                'metrics_history': self.metrics_history,
                'alerts': self.alerts,
                'thresholds': self.thresholds
            }
            
            try:
                with open(report_file, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
                print(f"📄 Metrics report saved to: {report_file}")
            except Exception as e:
                print(f"❌ Failed to save report: {str(e)}")

    def run_load_test(self):
        """Run a load test and monitor the results"""
        print("🔥 Running Load Test with Real-Time Monitoring")
        print("=" * 60)
        
        # Start monitoring in background
        monitoring_thread = threading.Thread(target=self.background_monitoring)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        
        # Run load test
        endpoints = ['/health', '/docs', '/api/v1/contracts/history']
        concurrent_requests = 10
        duration_seconds = 60
        
        print(f"🎯 Target: {self.target_url}")
        print(f"📊 Endpoints: {endpoints}")
        print(f"🔢 Concurrent Requests: {concurrent_requests}")
        print(f"⏱️ Duration: {duration_seconds} seconds")
        print("\nStarting load test...\n")
        
        # Load test results
        results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': []
        }
        
        def make_request():
            """Make a single request"""
            endpoint = endpoints[results['total_requests'] % len(endpoints)]
            try:
                start_time = time.time()
                response = requests.get(f"{self.target_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                results['total_requests'] += 1
                results['response_times'].append((end_time - start_time) * 1000)
                
                if response.status_code == 200:
                    results['successful_requests'] += 1
                else:
                    results['failed_requests'] += 1
                    
            except Exception:
                results['total_requests'] += 1
                results['failed_requests'] += 1
                results['response_times'].append(10000)  # Timeout
        
        # Run concurrent requests
        import concurrent.futures
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            while time.time() - start_time < duration_seconds:
                futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
                concurrent.futures.wait(futures)
                time.sleep(0.1)  # Small delay
        
        # Calculate results
        if results['response_times']:
            avg_response_time = sum(results['response_times']) / len(results['response_times'])
            success_rate = (results['successful_requests'] / max(results['total_requests'], 1)) * 100
        else:
            avg_response_time = 0
            success_rate = 0
        
        print("\n" + "=" * 60)
        print("🎯 LOAD TEST RESULTS")
        print("=" * 60)
        print(f"📊 Total Requests:     {results['total_requests']}")
        print(f"✅ Successful:         {results['successful_requests']}")
        print(f"❌ Failed:             {results['failed_requests']}")
        print(f"📈 Success Rate:       {success_rate:.1f}%")
        print(f"⚡ Avg Response Time:  {avg_response_time:.1f}ms")
        print(f"🚀 Requests/Second:    {results['total_requests'] / duration_seconds:.1f}")

    def background_monitoring(self):
        """Run monitoring in background during load test"""
        for _ in range(12):  # Monitor for 60 seconds (12 * 5)
            system_metrics, app_metrics = self.collect_metrics()
            new_alerts = self.check_alerts(system_metrics, app_metrics)
            time.sleep(5)

def main():
    """Main execution function"""
    print("📊 SoliVolt Real-Time Monitoring Dashboard")
    print("=========================================")
    
    monitor = SoliVoltMonitor()
    
    while True:
        print("\n🎮 Choose monitoring mode:")
        print("1. Real-Time Dashboard")
        print("2. Load Test with Monitoring")
        print("3. One-Time Health Check")
        print("4. View System Info")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            monitor.start_monitoring()
        elif choice == '2':
            monitor.run_load_test()
        elif choice == '3':
            system_metrics, app_metrics = monitor.collect_metrics()
            alerts = monitor.check_alerts(system_metrics, app_metrics)
            monitor.render_dashboard(system_metrics, app_metrics, alerts)
            input("\nPress Enter to continue...")
        elif choice == '4':
            print("\n💻 System Information:")
            print(f"CPU Cores: {psutil.cpu_count()}")
            print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
            print(f"Platform: {os.name}")
            input("\nPress Enter to continue...")
        elif choice == '5':
            print("👋 Monitoring complete!")
            break
        else:
            print("❌ Invalid choice, please try again.")

if __name__ == "__main__":
    # Install required packages if not available
    try:
        import psutil
        import requests
    except ImportError:
        print("📦 Installing required packages...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'psutil', 'requests'])
        import psutil
        import requests
    
    main()
