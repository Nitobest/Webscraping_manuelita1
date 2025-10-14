"""
Structured Logging and Monitoring Module

This module provides structured logging and basic monitoring capabilities
for the Manuelita scraper pipeline.
"""

import logging
import structlog
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass, field

from .config import LoggingConfig, MonitoringConfig


@dataclass
class MetricsCollector:
    """Collects and stores metrics for monitoring."""
    
    start_time: float = field(default_factory=time.time)
    counters: Dict[str, int] = field(default_factory=dict)
    timings: Dict[str, list[float]] = field(default_factory=dict)
    errors: list[Dict[str, Any]] = field(default_factory=list)
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self.counters[name] = self.counters.get(name, 0) + value
    
    def record_timing(self, name: str, duration: float) -> None:
        """Record a timing metric."""
        if name not in self.timings:
            self.timings[name] = []
        self.timings[name].append(duration)
    
    def record_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Record an error for monitoring."""
        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'message': message,
            'context': context or {}
        }
        self.errors.append(error_data)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics."""
        current_time = time.time()
        duration = current_time - self.start_time
        
        timing_summaries = {}
        for name, times in self.timings.items():
            if times:
                timing_summaries[name] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
        
        return {
            'total_duration': duration,
            'counters': self.counters.copy(),
            'timings': timing_summaries,
            'error_count': len(self.errors),
            'errors': self.errors[-10:] if self.errors else []  # Last 10 errors
        }


class StructuredLogger:
    """Structured logger with monitoring integration."""
    
    def __init__(self, logging_config: LoggingConfig, monitoring_config: MonitoringConfig):
        self.logging_config = logging_config
        self.monitoring_config = monitoring_config
        self.metrics = MetricsCollector() if monitoring_config.metrics_enabled else None
        
        # Configure structlog
        self._configure_logging()
        self.logger = structlog.get_logger()
    
    def _configure_logging(self) -> None:
        """Configure structlog with appropriate processors and formatters."""
        
        # Create log directory if it doesn't exist
        log_path = Path(self.logging_config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure standard library logging first
        logging.basicConfig(
            format="%(message)s",
            level=getattr(logging, self.logging_config.level),
            handlers=self._create_handlers()
        )
        
        # Configure structlog processors based on format
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ]
        
        if self.logging_config.format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.extend([
                structlog.dev.ConsoleRenderer(colors=True),
            ])
        
        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, self.logging_config.level)
            ),
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    def _create_handlers(self) -> list[logging.Handler]:
        """Create logging handlers based on configuration."""
        handlers = []
        
        # File handler
        file_handler = logging.FileHandler(self.logging_config.file_path, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
        
        # Console handler (if enabled)
        if self.logging_config.console_output:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            handlers.append(console_handler)
        
        return handlers
    
    def bind(self, **kwargs) -> structlog.BoundLogger:
        """Bind context to the logger."""
        return self.logger.bind(**kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)
        if self.metrics and self.monitoring_config.metrics_enabled:
            self.metrics.increment_counter('log_info')
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)
        if self.metrics and self.monitoring_config.metrics_enabled:
            self.metrics.increment_counter('log_debug')
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)
        if self.metrics and self.monitoring_config.metrics_enabled:
            self.metrics.increment_counter('log_warning')
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with optional exception."""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
        
        self.logger.error(message, **kwargs)
        
        if self.metrics and self.monitoring_config.error_tracking:
            error_type = kwargs.get('error_type', 'UnknownError')
            self.metrics.record_error(error_type, message, kwargs)
            self.metrics.increment_counter('errors')
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message."""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
        
        self.logger.critical(message, **kwargs)
        
        if self.metrics and self.monitoring_config.error_tracking:
            error_type = kwargs.get('error_type', 'CriticalError')
            self.metrics.record_error(error_type, message, kwargs)
            self.metrics.increment_counter('critical_errors')
    
    @contextmanager
    def timed_operation(self, operation_name: str, **context):
        """Context manager to time operations and log performance."""
        start_time = time.time()
        bound_logger = self.logger.bind(operation=operation_name, **context)
        
        try:
            bound_logger.info(f"Starting {operation_name}")
            yield bound_logger
            
        except Exception as e:
            duration = time.time() - start_time
            bound_logger.error(
                f"Failed {operation_name}",
                duration=duration,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            if self.metrics and self.monitoring_config.error_tracking:
                self.metrics.record_error(type(e).__name__, str(e), context)
                self.metrics.increment_counter(f'{operation_name}_errors')
            
            raise
        
        else:
            duration = time.time() - start_time
            bound_logger.info(f"Completed {operation_name}", duration=duration)
            
            if self.metrics and self.monitoring_config.performance_tracking:
                self.metrics.record_timing(operation_name, duration)
                self.metrics.increment_counter(f'{operation_name}_success')
    
    def increment_counter(self, counter_name: str, value: int = 1) -> None:
        """Increment a metric counter."""
        if self.metrics and self.monitoring_config.metrics_enabled:
            self.metrics.increment_counter(counter_name, value)
    
    def get_metrics_summary(self) -> Optional[Dict[str, Any]]:
        """Get a summary of collected metrics."""
        if self.metrics:
            return self.metrics.get_summary()
        return None
    
    def log_metrics_summary(self) -> None:
        """Log a summary of collected metrics."""
        if self.metrics:
            summary = self.metrics.get_summary()
            self.info("Metrics Summary", **summary)


# Global logger instance
_logger: Optional[StructuredLogger] = None


def init_logging(logging_config: LoggingConfig, monitoring_config: MonitoringConfig) -> StructuredLogger:
    """Initialize the global logger."""
    global _logger
    _logger = StructuredLogger(logging_config, monitoring_config)
    return _logger


def get_logger() -> StructuredLogger:
    """Get the global logger instance."""
    if _logger is None:
        from .config import get_config
        config = get_config()
        return init_logging(config.logging, config.monitoring)
    return _logger


def setup_logging_from_config(environment: str = "development") -> StructuredLogger:
    """Setup logging from configuration file."""
    from .config import init_config
    config = init_config(environment)
    return init_logging(config.logging, config.monitoring)