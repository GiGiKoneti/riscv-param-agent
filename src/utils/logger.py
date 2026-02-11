"""
Professional logging system for RISC-V Parameter Extractor.

This module provides structured logging with Rich formatting and
configurable output levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console


# Global logger registry
_loggers = {}


def setup_logger(
    name: str,
    level: str = "INFO",
    use_rich: bool = True,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with Rich formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_rich: Use Rich formatting
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    # Return existing logger if already configured
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    if use_rich:
        console = Console(stderr=True)
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
            show_time=True,
            show_path=False
        )
        formatter = logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
    else:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Cache logger
    _loggers[name] = logger
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)


def configure_logging_from_config(config) -> None:
    """
    Configure logging from config object.
    
    Args:
        config: Configuration object with logging settings
    """
    level = config.logging.level
    use_rich = config.logging.format == "rich"
    log_file = config.logging.file
    
    # Configure root logger
    setup_logger("riscv_extractor", level, use_rich, log_file)


# Convenience function for quick logger setup
def quick_logger(name: str = "riscv_extractor") -> logging.Logger:
    """
    Quick logger setup with defaults.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return setup_logger(name, level="INFO", use_rich=True)
