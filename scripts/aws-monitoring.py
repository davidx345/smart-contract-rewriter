#!/usr/bin/env python3
"""
📊 AWS EC2 Microservices Monitor
Real-time monitoring for AWS EC2 deployed microservices
"""

import os
import sys
import time
import json
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess

class MicroservicesMonitor:
    """
    Real-time monitoring for AWS EC2 microservices
    """
    
    def __init__(self):
        # AWS EC2 configuration
        self.ec2_host = os.getenv('EC2_HOST', 'localhost')
        self.services = {
            'unified_main': {
                'port': 8000,
                'health_endpoint': '/health',
                'name': 'Unified Main API'
            },
            'contract_service': {
                'port': 8001,
                'health_endpoint': '/health',
                'name': 'Contract Service'
            },
            'frontend': {
                'port': 3000,
                'health_endpoint': '/',
                'name': 'Frontend (if local)'
            }
        }
        
        self.metrics_history = []
        self.alerts = []
        self.running = False
        
        # AWS EC2 optimized thresholds
        self.thresholds = {
            'cpu_percent': 80.0,      # Higher for dedicated EC2
            'memory_percent': 85.0,   # More memory available
            'disk_percent': 90.0,     # EBS storage
            'response_time': 2.0,     # Target response time in seconds
            'error_rate': 5.0         # Max error rate percentage
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'memory_available_mb': memory.available // (1024 * 1024),
                'disk_free_gb': disk.free // (1024 * 1024 * 1024),
                'load_avg': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
            }
        except Exception as e:
            print(f"Error getting system metrics: {e}")
            return {}
    
    def check_service_health(self, service_name: str, config: Dict) -> Dict[str, Any]:
        """Check health of a specific service"""
        url = f"http://{self.ec2_host}:{config['port']}{config['health_endpoint']}"
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            response_time = time.time() - start_time
            
            return {
                'service': service_name,
                'name': config['name'],
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response_time,
                'status_code': response.status_code,
                'url': url
            }
        except requests.exceptions.RequestException as e:
            return {
                'service': service_name,
                'name': config['name'], 
                'status': 'down',
                'error': str(e),
                'url': url
            }
    
    def check_all_services(self) -> List[Dict[str, Any]]:
        """Check health of all services"""
        results = []
        for service_name, config in self.services.items():
            result = self.check_service_health(service_name, config)
            results.append(result)
        return results
    
    def check_docker_containers(self) -> List[Dict[str, Any]]:
        """Check Docker container status"""
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True, check=True)
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    container = json.loads(line)
                    containers.append({
                        'name': container.get('Names', 'Unknown'),
                        'status': container.get('Status', 'Unknown'),
                        'image': container.get('Image', 'Unknown'),
                        'ports': container.get('Ports', 'None')
                    })
            return containers
        except Exception as e:
            return [{'error': f'Docker check failed: {e}'}]
    
    def generate_alerts(self, metrics: Dict, services: List[Dict]) -> List[str]:
        """Generate alerts based on metrics and service status"""
        alerts = []
        
        # System resource alerts
        if metrics.get('cpu_percent', 0) > self.thresholds['cpu_percent']:
            alerts.append(f"🔥 HIGH CPU: {metrics['cpu_percent']:.1f}%")
        
        if metrics.get('memory_percent', 0) > self.thresholds['memory_percent']:
            alerts.append(f"🧠 HIGH MEMORY: {metrics['memory_percent']:.1f}%")
        
        if metrics.get('disk_percent', 0) > self.thresholds['disk_percent']:
            alerts.append(f"💾 HIGH DISK: {metrics['disk_percent']:.1f}%")
        
        # Service health alerts
        for service in services:
            if service.get('status') != 'healthy':
                alerts.append(f"🚨 SERVICE DOWN: {service['name']}")
            elif service.get('response_time', 0) > self.thresholds['response_time']:
                alerts.append(f"⏰ SLOW RESPONSE: {service['name']} ({service['response_time']:.2f}s)")
        
        return alerts
    
    def display_dashboard(self):
        """Display real-time monitoring dashboard"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 70)
        print("🚀 AWS EC2 MICROSERVICES MONITOR")
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Host: {self.ec2_host}")
        print("=" * 70)
        
        # System metrics
        metrics = self.get_system_metrics()
        if metrics:
            print("\n📊 SYSTEM METRICS:")
            print(f"  CPU: {metrics['cpu_percent']:.1f}%")
            print(f"  Memory: {metrics['memory_percent']:.1f}% ({metrics['memory_available_mb']} MB available)")
            print(f"  Disk: {metrics['disk_percent']:.1f}% ({metrics['disk_free_gb']} GB free)")
            if 'load_avg' in metrics:
                print(f"  Load: {metrics['load_avg']:.2f}")
        
        # Service health
        services = self.check_all_services()
        print("\n🏥 SERVICE HEALTH:")
        for service in services:
            status_icon = "✅" if service['status'] == 'healthy' else "❌"
            name = service['name']
            status = service['status'].upper()
            response_time = service.get('response_time', 0)
            
            if service['status'] == 'healthy':
                print(f"  {status_icon} {name}: {status} ({response_time:.3f}s)")
            else:
                error = service.get('error', 'Unknown error')
                print(f"  {status_icon} {name}: {status} - {error}")
        
        # Docker containers
        containers = self.check_docker_containers()
        if containers and not containers[0].get('error'):
            print("\n🐳 DOCKER CONTAINERS:")
            for container in containers:
                print(f"  📦 {container['name']}: {container['status']}")
        
        # Alerts
        alerts = self.generate_alerts(metrics, services)
        if alerts:
            print("\n🚨 ALERTS:")
            for alert in alerts:
                print(f"  {alert}")
        else:
            print("\n✅ ALL SYSTEMS HEALTHY")
        
        # Historical metrics
        self.metrics_history.append({
            'timestamp': datetime.now(),
            'metrics': metrics,
            'services': services,
            'alerts': alerts
        })
        
        # Keep last 60 entries (1 hour if checking every minute)
        if len(self.metrics_history) > 60:
            self.metrics_history.pop(0)
        
        print(f"\n📈 History: {len(self.metrics_history)} entries")
    
    def run_continuous_monitoring(self, interval: int = 30):
        """Run continuous monitoring with specified interval"""
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        self.running = True
        try:
            while self.running:
                self.display_dashboard()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            self.running = False
    
    def run_health_check(self):
        """Run a single health check"""
        print("🔍 Running health check...")
        
        # System metrics
        metrics = self.get_system_metrics()
        print(f"System CPU: {metrics.get('cpu_percent', 0):.1f}%")
        print(f"System Memory: {metrics.get('memory_percent', 0):.1f}%")
        print(f"System Disk: {metrics.get('disk_percent', 0):.1f}%")
        
        # Service health
        services = self.check_all_services()
        healthy_services = sum(1 for s in services if s['status'] == 'healthy')
        print(f"Services: {healthy_services}/{len(services)} healthy")
        
        for service in services:
            status_icon = "✅" if service['status'] == 'healthy' else "❌"
            print(f"  {status_icon} {service['name']}: {service['status']}")
        
        # Overall health
        all_healthy = all(s['status'] == 'healthy' for s in services)
        if all_healthy:
            print("\n✅ All systems operational")
            return True
        else:
            print("\n❌ Some services need attention")
            return False
    
    def generate_report(self) -> str:
        """Generate a monitoring report"""
        if not self.metrics_history:
            return "No monitoring data available"
        
        report = []
        report.append("📊 MICROSERVICES MONITORING REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Data points: {len(self.metrics_history)}")
        
        if self.metrics_history:
            latest = self.metrics_history[-1]
            report.append(f"\nLatest Status:")
            report.append(f"  CPU: {latest['metrics'].get('cpu_percent', 0):.1f}%")
            report.append(f"  Memory: {latest['metrics'].get('memory_percent', 0):.1f}%")
            report.append(f"  Disk: {latest['metrics'].get('disk_percent', 0):.1f}%")
            
            healthy_services = sum(1 for s in latest['services'] if s['status'] == 'healthy')
            total_services = len(latest['services'])
            report.append(f"  Services: {healthy_services}/{total_services} healthy")
            
            if latest['alerts']:
                report.append(f"\nActive Alerts:")
                for alert in latest['alerts']:
                    report.append(f"  - {alert}")
        
        return "\n".join(report)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AWS EC2 Microservices Monitor")
    parser.add_argument('--host', default='localhost', help='EC2 host IP')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=30, help='Monitoring interval in seconds')
    parser.add_argument('--report', action='store_true', help='Generate monitoring report')
    
    args = parser.parse_args()
    
    monitor = MicroservicesMonitor()
    if args.host != 'localhost':
        monitor.ec2_host = args.host
    
    if args.continuous:
        monitor.run_continuous_monitoring(args.interval)
    elif args.report:
        print(monitor.generate_report())
    else:
        healthy = monitor.run_health_check()
        sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    main()
