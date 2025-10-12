"""Connection interface for abstracting SSH and other remote connections."""

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


class ConnectionResult:
    """Result of a command execution."""

    def __init__(self, stdout: str, stderr: str, return_code: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.success = return_code == 0 and not stderr.strip()


class IConnection(ABC):
    """Abstract interface for remote connections."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection. Returns True if successful."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection and cleanup resources."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""

    @abstractmethod
    def execute_command(self, command: str, timeout: int | None = None) -> ConnectionResult:
        """Execute command and return result."""

    @contextmanager
    def session(self) -> Generator["IConnection"]:
        """Context manager for automatic connection lifecycle."""
        try:
            if not self.is_connected():
                self.connect()
            yield self
        finally:
            self.disconnect()


class IConnectionFactory(ABC):
    """Factory for creating connection instances."""

    @abstractmethod
    def create_connection(self, config: Any) -> IConnection:
        """Create connection instance from configuration."""
