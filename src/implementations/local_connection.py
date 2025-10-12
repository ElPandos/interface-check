"""Local connection implementation for running commands locally."""

import logging
import subprocess
import time
from typing import Any

from src.core.lifecycle import ILifecycleAware
from src.interfaces.connection import ConnectionResult, IConnection, IConnectionFactory

logger = logging.getLogger(__name__)


class LocalConnection(IConnection, ILifecycleAware):
    """Local command execution implementation."""

    def __init__(self, working_directory: str = "/"):
        self._working_directory = working_directory
        self._connected = False

    def initialize(self) -> None:
        """Initialize local connection."""
        self.connect()

    def cleanup(self) -> None:
        """Clean up local connection."""
        self.disconnect()

    def connect(self) -> bool:
        """Establish local connection (always succeeds)."""
        self._connected = True
        logger.debug("Local connection established")
        return True

    def disconnect(self) -> None:
        """Close local connection."""
        self._connected = False
        logger.debug("Local connection closed")

    def is_connected(self) -> bool:
        """Check if local connection is active."""
        return self._connected

    def execute_command(self, command: str, timeout: int | None = None) -> ConnectionResult:
        """Execute command locally."""
        if not self.is_connected():
            return ConnectionResult("", "Not connected", -1)

        try:
            start_time = time.perf_counter()

            # Split command for security (no shell injection)

            import shlex

            cmd_args = shlex.split(command)

            result = subprocess.run(  # noqa: S603
                cmd_args,
                check=False,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._working_directory,
            )

            execution_time = time.perf_counter() - start_time
            logger.debug(f"Local command executed in {execution_time:.2f}s: {command}")

            return ConnectionResult(result.stdout, result.stderr, result.returncode)

        except subprocess.TimeoutExpired:
            logger.warning(f"Local command timed out: {command}")
            return ConnectionResult("", f"Command timed out after {timeout}s", -1)
        except Exception as e:
            logger.exception(f"Local command failed: {command}")
            return ConnectionResult("", f"Execution error: {e}", -1)


class LocalConnectionFactory(IConnectionFactory):
    """Factory for creating local connections."""

    def create_connection(self, config: Any = None) -> IConnection:
        """Create local connection."""
        working_dir = getattr(config, "working_directory", "/") if config else "/"
        return LocalConnection(working_dir)
