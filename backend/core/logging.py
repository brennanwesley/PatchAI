"""
Enhanced logging with correlation IDs and structured data
"""

import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional


class StructuredLogger:
    """Enhanced logging with correlation IDs and structured data"""
    
    def __init__(self):
        # Configure structured logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Performance metrics storage
        self.metrics = {
            'requests_total': 0,
            'requests_by_endpoint': defaultdict(int),
            'response_times': defaultdict(list),
            'errors_total': 0,
            'errors_by_type': defaultdict(int),
            'openai_requests': 0,
            'openai_errors': 0,
            'rate_limit_hits': 0
        }
        
        self.logger.info("Structured logger initialized with performance metrics")
    
    def log_request(self, correlation_id: str, method: str, path: str, client_ip: str, user_id: str = None):
        """Log incoming request with structured data"""
        self.metrics['requests_total'] += 1
        self.metrics['requests_by_endpoint'][path] += 1
        
        log_data = {
            'correlation_id': correlation_id,
            'event': 'request_start',
            'method': method,
            'path': path,
            'client_ip': client_ip,
            'user_id': user_id,
            'timestamp': time.time()
        }
        
        self.logger.info(f"REQUEST_START | {correlation_id} | {method} {path} | IP: {client_ip} | User: {user_id}")
    
    def log_response(self, correlation_id: str, status_code: int, response_time_ms: float, endpoint: str):
        """Log response with performance metrics"""
        # Store response time for metrics (keep only recent 100 for memory efficiency)
        if len(self.metrics['response_times'][endpoint]) >= 100:
            self.metrics['response_times'][endpoint].pop(0)
        self.metrics['response_times'][endpoint].append(response_time_ms)
        
        log_data = {
            'correlation_id': correlation_id,
            'event': 'request_end',
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            'endpoint': endpoint,
            'timestamp': time.time()
        }
        
        self.logger.info(f"REQUEST_END | {correlation_id} | {status_code} | {response_time_ms:.2f}ms | {endpoint}")
    
    def log_error(self, correlation_id: str, error_type: str, error_message: str, user_id: str = None, stack_trace: str = None):
        """Log error with detailed context"""
        self.metrics['errors_total'] += 1
        self.metrics['errors_by_type'][error_type] += 1
        
        log_data = {
            'correlation_id': correlation_id,
            'event': 'error',
            'error_type': error_type,
            'error_message': error_message,
            'user_id': user_id,
            'timestamp': time.time()
        }
        
        error_msg = f"ERROR | {correlation_id} | {error_type} | {error_message} | User: {user_id}"
        if stack_trace:
            error_msg += f" | Stack: {stack_trace}"
        
        self.logger.error(error_msg)
    
    def log_openai_request(self, correlation_id: str, model: str, message_count: int):
        """Log OpenAI API request"""
        self.metrics['openai_requests'] += 1
        
        self.logger.info(f"OPENAI_REQUEST | {correlation_id} | Model: {model} | Messages: {message_count}")
    
    def log_openai_error(self, correlation_id: str, error: str):
        """Log OpenAI API error"""
        self.metrics['openai_errors'] += 1
        
        self.logger.error(f"OPENAI_ERROR | {correlation_id} | {error}")
    
    def log_rate_limit_hit(self, correlation_id: str, limit_type: str, user_id: str, client_ip: str):
        """Log rate limit hit"""
        self.metrics['rate_limit_hits'] += 1
        
        self.logger.warning(f"RATE_LIMIT_HIT | {correlation_id} | Type: {limit_type} | User: {user_id} | IP: {client_ip}")
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics"""
        # Calculate average response times
        avg_response_times = {}
        for endpoint, times in self.metrics['response_times'].items():
            if times:
                avg_response_times[endpoint] = sum(times) / len(times)
            else:
                avg_response_times[endpoint] = 0
        
        return {
            'requests_total': self.metrics['requests_total'],
            'requests_by_endpoint': dict(self.metrics['requests_by_endpoint']),
            'avg_response_times_ms': avg_response_times,
            'errors_total': self.metrics['errors_total'],
            'errors_by_type': dict(self.metrics['errors_by_type']),
            'openai_requests': self.metrics['openai_requests'],
            'openai_errors': self.metrics['openai_errors'],
            'rate_limit_hits': self.metrics['rate_limit_hits']
        }
