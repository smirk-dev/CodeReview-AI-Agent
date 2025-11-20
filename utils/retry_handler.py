"""
Retry Handler for API Calls
Implements retry logic with exponential backoff for API rate limits
"""

import time
import functools
import logging
from typing import Callable, Any, Optional, Type, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff"""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, exception: Exception) -> bool:
        """Determine if exception is retryable"""
        # Check for common retryable errors
        error_str = str(exception).lower()
        
        retryable_patterns = [
            '429',  # Rate limit
            'too many requests',
            'resource_exhausted',
            'quota exceeded',
            'timeout',
            'connection',
            'network'
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)
    
    def retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                if attempt == self.config.max_retries:
                    logger.error(f"Max retries ({self.config.max_retries}) exceeded for {func.__name__}")
                    raise
                
                if not self.should_retry(e):
                    logger.warning(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                
                delay = self.calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed for {func.__name__}. "
                    f"Retrying in {delay:.2f}s... Error: {e}"
                )
                time.sleep(delay)
        
        raise last_exception

def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Decorator for adding retry logic to functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            handler = RetryHandler(config)
            return handler.retry(func, *args, **kwargs)
        
        return wrapper
    return decorator

class GracefulDegradation:
    """Provides fallback mechanisms when primary operations fail"""
    
    @staticmethod
    def get_ai_summary_fallback(
        code: str,
        metrics: dict,
        issues: list
    ) -> str:
        """Fallback summary when AI is unavailable"""
        return (
            f"Code analysis completed (offline mode). "
            f"Found {len(issues)} issues. "
            f"Lines of code: {metrics.get('lines_of_code', 'N/A')}. "
            f"Complexity: {metrics.get('total_complexity', 'N/A')}."
        )
    
    @staticmethod
    def get_security_analysis_fallback(vulnerabilities: list) -> str:
        """Fallback security analysis when AI is unavailable"""
        if not vulnerabilities:
            return "Security scan completed (offline mode). No vulnerabilities detected by static analysis."
        
        return (
            f"Security scan completed (offline mode). "
            f"Found {len(vulnerabilities)} potential vulnerabilities. "
            f"Manual review recommended."
        )
    
    @staticmethod
    def get_quality_review_fallback(
        quality_score: int,
        issues: list,
        strengths: list
    ) -> str:
        """Fallback quality review when AI is unavailable"""
        return (
            f"Quality assessment completed (offline mode). "
            f"Score: {quality_score}/100. "
            f"Found {len(issues)} improvement areas and {len(strengths)} strengths."
        )

# Global retry handler instance
default_retry_handler = RetryHandler()
