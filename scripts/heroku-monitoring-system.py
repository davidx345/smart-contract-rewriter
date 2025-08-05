#!/usr/bin/env python3
"""
📊 SoliVolt Heroku Monitoring & Alerting System
Real-time monitoring with Grafana, Prometheus, and custom metrics
"""

import os
import sys
import time
import json
import requests
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

class HerokuMonitoringSystem:
    """
    Comprehensive monitoring system for Heroku-deployed applications
    """
    
    def __init__(self):
        self.heroku_app_name = os.getenv('HEROKU_APP_NAME', 'solivolt-8e0565441715')
        self.heroku_api_key = os.getenv('HEROKU_API_KEY', '')
        self.app_url = f"https://{self.heroku_app_name}.herokuapp.com"
        
        # Monitoring configuration
        self.monitoring_interval = 30  # seconds
        self.alert_thresholds = {
            'response_time': 2000,     # 2 seconds
            'error_rate': 5.0,         # 5%
            'cpu_usage': 80.0,         # 80%
            'memory_usage': 85.0,      # 85%
            'availability': 95.0,      # 95%
        }
        
        # Alert channels
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')
        self.email_webhook = os.getenv('EMAIL_WEBHOOK_URL', '')
        
        # Metrics storage
        self.metrics_history = []
        self.alerts_sent = set()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitoring.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[32m",     # Green
            "WARN": "\033[33m",     # Yellow  
            "ERROR": "\033[31m",    # Red
            "ALERT": "\033[91m",    # Bright Red
            "SUCCESS": "\033[92m",  # Bright Green
            "RESET": "\033[0m"      # Reset
        }
        
        color = colors.get(level, colors["INFO"])
        print(f"{color}[{timestamp}] {message}{colors['RESET']}")
        
        # Also log to file
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARN":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def get_heroku_headers(self) -> Dict[str, str]:
        """Get standard Heroku API headers"""
        return {
            'Authorization': f'Bearer {self.heroku_api_key}',
            'Accept': 'application/vnd.heroku+json; version=3',
            'Content-Type': 'application/json'
        }
    
    def collect_app_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive application metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'app_name': self.heroku_app_name,
        }
        
        # Health check metrics
        health_metrics = self.check_app_health()
        metrics.update(health_metrics)
        
        # Heroku dyno metrics
        dyno_metrics = self.get_dyno_metrics()
        metrics.update(dyno_metrics)
        
        # Database metrics
        db_metrics = self.get_database_metrics()
        metrics.update(db_metrics)
        
        # Custom application metrics
        app_metrics = self.get_application_metrics()
        metrics.update(app_metrics)
        
        return metrics
    
    def check_app_health(self) -> Dict[str, Any]:
        """Check application health and response times"""
        endpoints = [
            ('/health', 'health_check'),
            ('/docs', 'documentation'),
            ('/api/v1/contracts/history', 'contract_history'),
        ]
        
        health_metrics = {}
        
        for endpoint, metric_name in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.app_url}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                health_metrics[f"{metric_name}_response_time"] = response_time
                health_metrics[f"{metric_name}_status_code"] = response.status_code
                health_metrics[f"{metric_name}_available"] = response.status_code < 400
                
            except Exception as e:
                health_metrics[f"{metric_name}_response_time"] = 0
                health_metrics[f"{metric_name}_status_code"] = 0
                health_metrics[f"{metric_name}_available"] = False
                health_metrics[f"{metric_name}_error"] = str(e)
        
        # Calculate overall availability
        available_endpoints = sum(1 for endpoint, _ in endpoints 
                                if health_metrics.get(f"{endpoint[1:]}_available", False))
        health_metrics['overall_availability'] = (available_endpoints / len(endpoints)) * 100
        
        return health_metrics
    
    def get_dyno_metrics(self) -> Dict[str, Any]:
        """Get Heroku dyno metrics"""
        if not self.heroku_api_key:
            return {}
        
        try:
            headers = self.get_heroku_headers()
            
            # Get dyno information
            dyno_response = requests.get(
                f'https://api.heroku.com/apps/{self.heroku_app_name}/dynos',
                headers=headers
            )
            
            if dyno_response.status_code != 200:
                return {'dyno_metrics_error': 'Failed to fetch dyno info'}
            
            dynos = dyno_response.json()
            
            dyno_metrics = {
                'dyno_count': len(dynos),
                'dynos_up': sum(1 for dyno in dynos if dyno['state'] == 'up'),
                'dynos_down': sum(1 for dyno in dynos if dyno['state'] == 'down'),
                'dynos_crashed': sum(1 for dyno in dynos if dyno['state'] == 'crashed'),
            }
            
            # Get formation (scaling) info
            formation_response = requests.get(
                f'https://api.heroku.com/apps/{self.heroku_app_name}/formation',
                headers=headers
            )
            
            if formation_response.status_code == 200:
                formation = formation_response.json()
                for process in formation:
                    dyno_metrics[f"{process['type']}_quantity"] = process['quantity']
                    dyno_metrics[f"{process['type']}_size"] = process['size']
            
            return dyno_metrics
            
        except Exception as e:
            return {'dyno_metrics_error': str(e)}
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            # Test database connection through health endpoint
            response = requests.get(f"{self.app_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Extract database metrics if available
                db_metrics = {
                    'database_connected': health_data.get('database', {}).get('connected', False),
                    'database_response_time': health_data.get('database', {}).get('response_time', 0),
                }
                
                return db_metrics
            
            return {'database_connected': False}
            
        except Exception as e:
            return {'database_error': str(e)}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get custom application metrics"""
        try:
            # Try to get metrics from a custom endpoint (if it exists)
            response = requests.get(f"{self.app_url}/metrics", timeout=10)
            
            if response.status_code == 200:
                return response.json()
            
            # If no custom metrics endpoint, return basic stats
            return {
                'custom_metrics_available': False,
                'app_version': 'unknown'
            }
            
        except Exception:
            return {'custom_metrics_available': False}
    
    def check_alert_conditions(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any alert conditions are met"""
        alerts = []
        
        # Response time alerts
        if metrics.get('health_check_response_time', 0) > self.alert_thresholds['response_time']:
            alerts.append({
                'type': 'response_time',
                'severity': 'warning',
                'message': f"High response time: {metrics['health_check_response_time']:.1f}ms",
                'threshold': self.alert_thresholds['response_time'],
                'current_value': metrics['health_check_response_time']
            })
        
        # Availability alerts
        availability = metrics.get('overall_availability', 100)
        if availability < self.alert_thresholds['availability']:
            alerts.append({
                'type': 'availability',
                'severity': 'critical',
                'message': f"Low availability: {availability:.1f}%",
                'threshold': self.alert_thresholds['availability'],
                'current_value': availability
            })
        
        # Dyno alerts
        if metrics.get('dynos_crashed', 0) > 0:
            alerts.append({
                'type': 'dyno_crashed',
                'severity': 'critical',
                'message': f"Crashed dynos detected: {metrics['dynos_crashed']}",
                'current_value': metrics['dynos_crashed']
            })
        
        if metrics.get('dynos_down', 0) > 0:
            alerts.append({
                'type': 'dyno_down',
                'severity': 'warning',
                'message': f"Down dynos detected: {metrics['dynos_down']}",
                'current_value': metrics['dynos_down']
            })
        
        # Database alerts
        if not metrics.get('database_connected', True):
            alerts.append({
                'type': 'database',
                'severity': 'critical',
                'message': "Database connection failed",
                'current_value': False
            })
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert through configured channels"""
        alert_key = f"{alert['type']}_{alert.get('current_value', 'unknown')}"
        
        # Avoid duplicate alerts (cooldown period)
        if alert_key in self.alerts_sent:
            return
        
        self.alerts_sent.add(alert_key)
        
        # Remove from alerts_sent after 30 minutes to allow re-alerting
        threading.Timer(1800, lambda: self.alerts_sent.discard(alert_key)).start()
        
        severity_emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        emoji = severity_emoji.get(alert['severity'], '⚠️')
        message = f"{emoji} **SoliVolt Alert**\n{alert['message']}"
        
        self.log(f"🚨 ALERT: {alert['message']}", "ALERT")
        
        # Send to Slack
        if self.slack_webhook:
            self.send_slack_alert(message, alert)
        
        # Send to email (if configured)
        if self.email_webhook:
            self.send_email_alert(message, alert)
    
    def send_slack_alert(self, message: str, alert: Dict[str, Any]):
        """Send alert to Slack"""
        try:
            color = "danger" if alert['severity'] == 'critical' else "warning"
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"SoliVolt {alert['severity'].title()} Alert",
                        "text": message,
                        "fields": [
                            {
                                "title": "App",
                                "value": self.heroku_app_name,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            }
                        ],
                        "timestamp": int(datetime.now().timestamp())
                    }
                ]
            }
            
            requests.post(self.slack_webhook, json=payload, timeout=10)
            
        except Exception as e:
            self.log(f"Failed to send Slack alert: {str(e)}", "ERROR")
    
    def send_email_alert(self, message: str, alert: Dict[str, Any]):
        """Send alert via email webhook"""
        try:
            payload = {
                "subject": f"SoliVolt {alert['severity'].title()} Alert",
                "message": message,
                "app": self.heroku_app_name,
                "timestamp": datetime.now().isoformat()
            }
            
            requests.post(self.email_webhook, json=payload, timeout=10)
            
        except Exception as e:
            self.log(f"Failed to send email alert: {str(e)}", "ERROR")
    
    def generate_grafana_dashboard(self) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "SoliVolt Heroku Monitoring",
                "tags": ["solivolt", "heroku", "monitoring"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Response Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "solivolt_response_time",
                                "legendFormat": "Response Time (ms)"
                            }
                        ],
                        "yAxes": [
                            {
                                "label": "Milliseconds",
                                "min": 0
                            }
                        ],
                        "alert": {
                            "conditions": [
                                {
                                    "query": {
                                        "queryType": "",
                                        "refId": "A"
                                    },
                                    "reducer": {
                                        "type": "avg",
                                        "params": []
                                    },
                                    "evaluator": {
                                        "params": [2000],
                                        "type": "gt"
                                    }
                                }
                            ],
                            "executionErrorState": "alerting",
                            "for": "5m",
                            "frequency": "10s",
                            "handler": 1,
                            "name": "High Response Time",
                            "noDataState": "no_data",
                            "notifications": []
                        }
                    },
                    {
                        "id": 2,
                        "title": "Availability",
                        "type": "singlestat",
                        "targets": [
                            {
                                "expr": "solivolt_availability",
                                "legendFormat": "Availability %"
                            }
                        ],
                        "valueName": "current",
                        "format": "percent",
                        "thresholds": "95,99",
                        "colorBackground": True
                    },
                    {
                        "id": 3,
                        "title": "Dyno Status",
                        "type": "table",
                        "targets": [
                            {
                                "expr": "solivolt_dynos_up",
                                "legendFormat": "Up"
                            },
                            {
                                "expr": "solivolt_dynos_down", 
                                "legendFormat": "Down"
                            },
                            {
                                "expr": "solivolt_dynos_crashed",
                                "legendFormat": "Crashed"
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "solivolt_error_rate",
                                "legendFormat": "Error Rate %"
                            }
                        ],
                        "yAxes": [
                            {
                                "label": "Percentage",
                                "min": 0,
                                "max": 100
                            }
                        ]
                    }
                ],
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": "5s"
            },
            "overwrite": True
        }
        
        return dashboard
    
    def export_metrics_to_prometheus(self, metrics: Dict[str, Any]):
        """Export metrics in Prometheus format"""
        prometheus_metrics = []
        
        # Convert metrics to Prometheus format
        for key, value in metrics.items():
            if isinstance(value, (int, float, bool)):
                metric_value = 1 if isinstance(value, bool) and value else (0 if isinstance(value, bool) else value)
                prometheus_metrics.append(f"solivolt_{key} {metric_value}")
        
        return "\n".join(prometheus_metrics)
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.log("🎯 Starting continuous monitoring...", "INFO")
        
        while True:
            try:
                # Collect metrics
                metrics = self.collect_app_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Check for alerts
                alerts = self.check_alert_conditions(metrics)
                
                # Send alerts
                for alert in alerts:
                    self.send_alert(alert)
                
                # Log current status
                availability = metrics.get('overall_availability', 0)
                response_time = metrics.get('health_check_response_time', 0)
                dynos_up = metrics.get('dynos_up', 0)
                
                status_message = (f"📊 Status: {availability:.1f}% available, "
                                f"{response_time:.1f}ms response, {dynos_up} dynos up")
                
                if alerts:
                    self.log(f"{status_message} - {len(alerts)} alerts", "WARN")
                else:
                    self.log(status_message, "INFO")
                
                # Export metrics (could be sent to Prometheus here)
                prometheus_metrics = self.export_metrics_to_prometheus(metrics)
                
                # Save metrics to file for external consumption
                with open('metrics.txt', 'w') as f:
                    f.write(prometheus_metrics)
                
                time.sleep(self.monitoring_interval)
                
            except KeyboardInterrupt:
                self.log("👋 Monitoring stopped by user", "INFO")
                break
            except Exception as e:
                self.log(f"❌ Monitoring error: {str(e)}", "ERROR")
                time.sleep(self.monitoring_interval)
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 readings
        
        # Calculate averages
        avg_response_time = sum(m.get('health_check_response_time', 0) for m in recent_metrics) / len(recent_metrics)
        avg_availability = sum(m.get('overall_availability', 0) for m in recent_metrics) / len(recent_metrics)
        
        # Check for issues
        issues = []
        if avg_response_time > self.alert_thresholds['response_time']:
            issues.append(f"High average response time: {avg_response_time:.1f}ms")
        
        if avg_availability < self.alert_thresholds['availability']:
            issues.append(f"Low availability: {avg_availability:.1f}%")
        
        latest_metrics = recent_metrics[-1] if recent_metrics else {}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": min(100, avg_availability),
            "avg_response_time": avg_response_time,
            "avg_availability": avg_availability,
            "dynos_status": {
                "up": latest_metrics.get('dynos_up', 0),
                "down": latest_metrics.get('dynos_down', 0),
                "crashed": latest_metrics.get('dynos_crashed', 0)
            },
            "database_connected": latest_metrics.get('database_connected', False),
            "issues": issues,
            "recommendations": self.get_health_recommendations(latest_metrics, issues)
        }
    
    def get_health_recommendations(self, metrics: Dict[str, Any], issues: List[str]) -> List[str]:
        """Get health improvement recommendations"""
        recommendations = []
        
        if metrics.get('health_check_response_time', 0) > 1000:
            recommendations.append("Consider optimizing database queries and API endpoints")
        
        if metrics.get('dynos_crashed', 0) > 0:
            recommendations.append("Investigate and fix application crashes")
        
        if not metrics.get('database_connected', True):
            recommendations.append("Check database connection and credentials")
        
        if metrics.get('overall_availability', 100) < 95:
            recommendations.append("Review error logs and implement health check improvements")
        
        if not recommendations:
            recommendations.append("Application health looks good! 🎉")
        
        return recommendations

def main():
    """Main function"""
    print("📊 SoliVolt Heroku Monitoring System")
    print("=" * 50)
    
    monitor = HerokuMonitoringSystem()
    
    while True:
        print("\n📊 Monitoring Menu:")
        print("1. 🎯 Start Continuous Monitoring")
        print("2. 📈 Collect Current Metrics")
        print("3. 🚨 Check Alert Conditions")
        print("4. 📋 Generate Health Report")
        print("5. 📊 Export Grafana Dashboard")
        print("6. ⚙️ Configure Alert Thresholds")
        print("7. 📁 View Metrics History")
        print("8. 🧪 Test Alert System")
        print("9. 🚪 Exit")
        
        choice = input("\nChoose monitoring option (1-9): ").strip()
        
        if choice == '1':
            monitor.start_monitoring()
        elif choice == '2':
            metrics = monitor.collect_app_metrics()
            print(json.dumps(metrics, indent=2))
        elif choice == '3':
            metrics = monitor.collect_app_metrics()
            alerts = monitor.check_alert_conditions(metrics)
            if alerts:
                print("🚨 Active alerts:")
                for alert in alerts:
                    print(f"  - {alert['message']}")
            else:
                print("✅ No alerts detected")
        elif choice == '4':
            report = monitor.generate_health_report()
            print(json.dumps(report, indent=2))
        elif choice == '5':
            dashboard = monitor.generate_grafana_dashboard()
            with open('grafana-dashboard.json', 'w') as f:
                json.dump(dashboard, f, indent=2)
            print("✅ Grafana dashboard saved to grafana-dashboard.json")
        elif choice == '6':
            print("⚙️ Current thresholds:")
            for key, value in monitor.alert_thresholds.items():
                print(f"  {key}: {value}")
            # Could add threshold modification here
        elif choice == '7':
            if monitor.metrics_history:
                print(f"📁 Last {len(monitor.metrics_history)} metrics collected")
                latest = monitor.metrics_history[-1]
                print("Latest metrics:")
                print(json.dumps(latest, indent=2))
            else:
                print("📁 No metrics history available")
        elif choice == '8':
            test_alert = {
                'type': 'test',
                'severity': 'info',
                'message': 'Test alert from monitoring system',
                'current_value': 'test'
            }
            monitor.send_alert(test_alert)
            print("✅ Test alert sent")
        elif choice == '9':
            print("👋 Monitoring session complete!")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    main()
