"""
Logging utilities for the flowup-support-bot.
"""

import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """
    
    def format(self, record):
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted log entry
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra') and record.extra:
            log_entry.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)


class FlowupLogger:
    """
    Custom logger for Flowup applications.
    """
    
    def __init__(self, name: str, level: str = 'INFO', log_file: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            level: Log level
            log_file: Optional log file path
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.log_file = log_file
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add console handler
        self._add_console_handler()
        
        # Add file handler if specified
        if log_file:
            self._add_file_handler(log_file)
    
    def _add_console_handler(self):
        """Add console handler with JSON formatting."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self, log_file: str):
        """Add file handler with JSON formatting."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.level)
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)


# Global logger instances
_loggers: Dict[str, FlowupLogger] = {}


def setup_logger(name: str, level: str = 'INFO', log_file: Optional[str] = None) -> FlowupLogger:
    """
    Set up a logger instance.
    
    Args:
        name: Logger name
        level: Log level
        log_file: Optional log file path
        
    Returns:
        Logger instance
    """
    if name not in _loggers:
        _loggers[name] = FlowupLogger(name, level, log_file)
    
    return _loggers[name]


def get_logger(name: str) -> FlowupLogger:
    """
    Get an existing logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if name not in _loggers:
        _loggers[name] = FlowupLogger(name)
    
    return _loggers[name]


def configure_logging(config: Dict[str, Any]) -> None:
    """
    Configure logging based on configuration.
    
    Args:
        config: Logging configuration
    """
    log_level = config.get('log_level', 'INFO')
    log_file = config.get('log_file')
    
    # Set up root logger
    root_logger = setup_logger('root', log_level, log_file)
    
    # Set up specific loggers
    loggers_config = config.get('loggers', {})
    for logger_name, logger_config in loggers_config.items():
        setup_logger(
            logger_name,
            logger_config.get('level', log_level),
            logger_config.get('file')
        )


class LogContext:
    """
    Context manager for adding context to logs.
    """
    
    def __init__(self, logger: FlowupLogger, **context):
        """
        Initialize log context.
        
        Args:
            logger: Logger instance
            **context: Context variables
        """
        self.logger = logger
        self.context = context
        self.original_handlers = []
    
    def __enter__(self):
        """Enter context."""
        # Store original handlers
        self.original_handlers = self.logger.logger.handlers.copy()
        
        # Add context to all handlers
        for handler in self.logger.logger.handlers:
            if isinstance(handler.formatter, JSONFormatter):
                # Add context to formatter
                handler.formatter.context = self.context
        
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        # Restore original handlers
        self.logger.logger.handlers = self.original_handlers


def log_function_call(func):
    """
    Decorator to log function calls.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        logger.info(
            f"Calling function {func.__name__}",
            function=func.__name__,
            module=func.__module__,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )
        
        try:
            result = func(*args, **kwargs)
            logger.info(
                f"Function {func.__name__} completed successfully",
                function=func.__name__,
                module=func.__module__
            )
            return result
        except Exception as e:
            logger.error(
                f"Function {func.__name__} failed with error: {str(e)}",
                function=func.__name__,
                module=func.__module__,
                error=str(e)
            )
            raise
    
    return wrapper


def log_performance(func):
    """
    Decorator to log function performance.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.utcnow()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Function {func.__name__} completed in {duration:.3f}s",
                function=func.__name__,
                module=func.__module__,
                duration=duration
            )
            return result
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(
                f"Function {func.__name__} failed after {duration:.3f}s: {str(e)}",
                function=func.__name__,
                module=func.__module__,
                duration=duration,
                error=str(e)
            )
            raise
    
    return wrapper


def log_async_function_call(func):
    """
    Decorator to log async function calls.
    
    Args:
        func: Async function to decorate
        
    Returns:
        Decorated function
    """
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        logger.info(
            f"Calling async function {func.__name__}",
            function=func.__name__,
            module=func.__module__,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )
        
        try:
            result = await func(*args, **kwargs)
            logger.info(
                f"Async function {func.__name__} completed successfully",
                function=func.__name__,
                module=func.__module__
            )
            return result
        except Exception as e:
            logger.error(
                f"Async function {func.__name__} failed with error: {str(e)}",
                function=func.__name__,
                module=func.__module__,
                error=str(e)
            )
            raise
    
    return wrapper


def log_async_performance(func):
    """
    Decorator to log async function performance.
    
    Args:
        func: Async function to decorate
        
    Returns:
        Decorated function
    """
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.utcnow()
        
        try:
            result = await func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Async function {func.__name__} completed in {duration:.3f}s",
                function=func.__name__,
                module=func.__module__,
                duration=duration
            )
            return result
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(
                f"Async function {func.__name__} failed after {duration:.3f}s: {str(e)}",
                function=func.__name__,
                module=func.__module__,
                duration=duration,
                error=str(e)
            )
            raise
    
    return wrapper


def create_logger_for_module(module_name: str, level: str = 'INFO') -> FlowupLogger:
    """
    Create a logger for a specific module.
    
    Args:
        module_name: Module name
        level: Log level
        
    Returns:
        Logger instance
    """
    return setup_logger(module_name, level)


def get_module_logger(module_name: str) -> FlowupLogger:
    """
    Get a logger for a specific module.
    
    Args:
        module_name: Module name
        
    Returns:
        Logger instance
    """
    return get_logger(module_name)


def log_system_info(logger: FlowupLogger) -> None:
    """
    Log system information.
    
    Args:
        logger: Logger instance
    """
    import platform
    import psutil
    
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available
    }
    
    logger.info("System information", **system_info)


def log_configuration(logger: FlowupLogger, config: Dict[str, Any]) -> None:
    """
    Log configuration (excluding sensitive information).
    
    Args:
        logger: Logger instance
        config: Configuration dictionary
    """
    # Filter out sensitive information
    sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key']
    
    filtered_config = {}
    for key, value in config.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            filtered_config[key] = '***REDACTED***'
        elif isinstance(value, dict):
            filtered_config[key] = log_configuration(logger, value)
        else:
            filtered_config[key] = value
    
    logger.info("Configuration loaded", config=filtered_config)
