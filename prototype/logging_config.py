"""
Logging and metrics collection configuration for validation prototype.
Provides centralized logging setup and metrics tracking.
"""

import logging
# Import logging_util from the mvp_site package
from mvp_site import logging_util
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
import os

# Create logs directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


class MetricsCollector:
    """Collects and tracks performance metrics for validators."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
        
    def record_validation(self, validator_name: str, duration: float, 
                         success: bool, narrative_length: int):
        """Record a validation event."""
        if validator_name not in self.metrics:
            self.metrics[validator_name] = {
                "total_validations": 0,
                "successful_validations": 0,
                "failed_validations": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0,
                "total_narrative_length": 0,
                "errors": []
            }
        
        metrics = self.metrics[validator_name]
        metrics["total_validations"] += 1
        
        if success:
            metrics["successful_validations"] += 1
        else:
            metrics["failed_validations"] += 1
            
        metrics["total_duration"] += duration
        metrics["avg_duration"] = metrics["total_duration"] / metrics["total_validations"]
        metrics["min_duration"] = min(metrics["min_duration"], duration)
        metrics["max_duration"] = max(metrics["max_duration"], duration)
        metrics["total_narrative_length"] += narrative_length
        
    def record_error(self, validator_name: str, error: str):
        """Record an error event."""
        if validator_name not in self.metrics:
            self.metrics[validator_name] = {"errors": []}
            
        self.metrics[validator_name]["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error
        })
        
    def get_metrics(self, validator_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific validator or all validators."""
        if validator_name:
            return self.metrics.get(validator_name, {})
        
        return {
            "collection_started": datetime.fromtimestamp(self.start_time).isoformat(),
            "collection_duration": time.time() - self.start_time,
            "validators": self.metrics
        }
    
    def save_metrics(self, filepath: str):
        """Save metrics to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.get_metrics(), f, indent=2)
            
    def reset(self, validator_name: Optional[str] = None):
        """Reset metrics for a validator or all validators."""
        if validator_name:
            if validator_name in self.metrics:
                del self.metrics[validator_name]
        else:
            self.metrics = {}


# Global metrics collector instance
metrics_collector = MetricsCollector()


def setup_logging(name: str = "validation_prototype", 
                 level: int = logging.INFO,
                 log_to_file: bool = True) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        name: Logger name
        level: Logging level
        log_to_file: Whether to also log to file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if requested
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(LOG_DIR, f"{name}_{timestamp}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Log the log file location
        logger.info(f"Logging to file: {log_file}")
    
    return logger


def log_validation_event(logger: logging.Logger, event_type: str, 
                        details: Dict[str, Any]):
    """Log a structured validation event."""
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details
    }
    logger.info(f"Validation Event: {json.dumps(event)}")


def with_metrics(validator_name: str = None):
    """
    Decorator to automatically collect metrics for validation methods.
    
    Usage:
        @with_metrics("MyValidator")
        def validate(self, narrative_text, expected_entities, location):
            # validation logic
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract validator name if not provided
            name = validator_name
            if not name and hasattr(args[0], 'name'):
                name = args[0].name
            if not name:
                name = func.__name__
                
            # Get narrative length
            narrative_length = 0
            if len(args) > 1 and isinstance(args[1], str):
                narrative_length = len(args[1])
            elif 'narrative_text' in kwargs:
                narrative_length = len(kwargs['narrative_text'])
            
            # Time the execution
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                metrics_collector.record_error(name, str(e))
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_validation(
                    name, duration, success, narrative_length
                )
        
        return wrapper
    return decorator


# Set up default logger
default_logger = setup_logging()


class ValidationLogger:
    """Context manager for validation logging."""
    
    def __init__(self, test_name: str, logger: Optional[logging.Logger] = None):
        self.test_name = test_name
        self.logger = logger or default_logger
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting validation test: {self.test_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            self.logger.info(
                f"Completed validation test: {self.test_name} "
                f"(duration: {duration:.3f}s)"
            )
        else:
            logging_util.error(
                f"Failed validation test: {self.test_name} "
                f"(duration: {duration:.3f}s, error: {exc_val})",
                logger=self.logger
            )
        return False