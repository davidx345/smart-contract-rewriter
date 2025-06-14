from prometheus_client import Counter, Histogram, Gauge, generate_latest
from typing import Optional
import time

class MetricsService:
    """Service for collecting and exposing Prometheus metrics"""
    
    def __init__(self):
        # Request counters
        self.request_count = Counter(
            'smart_contract_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        # Request duration histogram
        self.request_duration = Histogram(
            'smart_contract_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Contract processing metrics
        self.contracts_analyzed = Counter(
            'smart_contract_analyzed_total',
            'Total number of contracts analyzed'
        )
        
        self.contracts_rewritten = Counter(
            'smart_contract_rewritten_total',
            'Total number of contracts rewritten'
        )
        
        # Gas optimization metrics
        self.gas_saved_total = Counter(
            'smart_contract_gas_saved_total',
            'Total gas saved through optimization'
        )
          # Active connections gauge
        self.active_connections = Gauge(
            'smart_contract_active_connections',
            'Number of active connections'
        )
        
        # Processing time histogram
        self.processing_time_histogram = Histogram(
            'smart_contract_processing_seconds',
            'Time spent processing contracts',
            ['operation_type']
        )
    
    def record_request(self, method: str, endpoint: str, status: int):
        """Record a request with method, endpoint, and status code"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()

    def record_request_duration(self, method: str, endpoint: str, duration: float):
        """Record request duration"""
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_contract_analyzed(self):
        """Increment contracts analyzed counter"""
        self.contracts_analyzed.inc()
    
    def record_contract_rewritten(self, gas_saved: Optional[int] = None):
        """Increment contracts rewritten counter and optionally record gas saved"""
        self.contracts_rewritten.inc()
        if gas_saved:
            self.gas_saved_total.inc(gas_saved)
    
    def record_processing_time(self, operation_type: str, duration: float):
        """Record processing time for different operations"""
        self.processing_time_histogram.labels(operation_type=operation_type).observe(duration)
    
    def set_active_connections(self, count: int):
        """Set the number of active connections"""
        self.active_connections.set(count)
    def track_contract_analysis(self, status: str, language: str):
        """Track contract analysis operations"""
        if status == "started":
            # Just increment a started counter or do nothing since we track completion
            pass
        elif status == "success":
            self.record_contract_analyzed()
        elif status == "failed":
            # Could track failed analyses if needed
            pass
    def track_error(self, error_type: str, location: str):
        """Track errors by type and location"""
        # Use existing error counter or create one if needed
        pass  # For now, just pass since we have basic error tracking
    
    def processing_time(self, operation_type: str):
        """Decorator for measuring processing time"""
        import functools
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.record_processing_time(operation_type, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.record_processing_time(f"{operation_type}_failed", duration)
                    raise
            return wrapper
        return decorator
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest()

# Global metrics service instance
metrics_service = MetricsService()