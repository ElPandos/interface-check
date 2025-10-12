"""Core framework components for dependency injection and lifecycle management."""

from .base import Cache, Component, Factory, Observer, Repository, Result, Service, SimpleCache, Subject, Validator
from .collector import CollectionManager, CollectionWorker, DataCollector, Sample
from .config import AppConfigManager, ConfigManager
from .connection import CommandResult, Connection, ConnectionConfig, JumpHostConnection, SshConnection
from .validation import ConfigValidator, HostValidator, InputValidator, NetworkValidator, sanitize_input, validate_ip

__all__ = [
    "AppConfigManager",
    "Cache",
    # Collection system
    "CollectionManager",
    "CollectionWorker",
    "CommandResult",
    # Base classes
    "Component",
    # Configuration
    "ConfigManager",
    "ConfigValidator",
    # Connection
    "Connection",
    "ConnectionConfig",
    "DataCollector",
    "Factory",
    "HostValidator",
    "InputValidator",
    "JumpHostConnection",
    # Validation
    "NetworkValidator",
    "Observer",
    "Repository",
    "Result",
    "Sample",
    "Service",
    "SimpleCache",
    "SshConnection",
    "Subject",
    "Validator",
    "sanitize_input",
    "validate_ip",
]
