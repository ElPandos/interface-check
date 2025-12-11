"""Base scanner model."""

import logging
import threading

from src.core.connect import SshConnection
from src.core.enum.messages import LogMsg
from src.core.worker import Worker, WorkerConfig, WorkManager
from src.interfaces.scanner import IScanner


class BaseScanner(IScanner):
    """Base class for scanner implementations."""

    def __init__(self, cfg, logger: logging.Logger, shutdown_event: threading.Event):
        """Initialize base scanner.

        Args:
            cfg: Configuration object
            logger: Logger instance
            shutdown_event: Shutdown event
        """
        self._cfg = cfg
        self._logger = logger
        self._shutdown_event = shutdown_event
        self._ssh: SshConnection | None = None
        self._worker_manager = WorkManager()

    @property
    def worker_manager(self) -> WorkManager:
        """Get worker manager.

        Returns:
            WorkManager: Worker manager instance
        """
        return self._worker_manager

    def disconnect(self) -> None:
        """Disconnect and clean up."""
        if self._ssh:
            self._ssh.disconnect()

    def _add_worker_to_manager(self, worker_cfg: WorkerConfig) -> None:
        """Add worker to manager.

        Args:
            worker_cfg: Worker configuration
        """
        self._logger.debug(f"{LogMsg.SCANNER_SUT_WORKER_CMD.value}: '{worker_cfg.command}'")
        shared_state = self._worker_manager.get_shared_flap_state()
        statistics = self._worker_manager.get_statistics()

        # Create SSH factory for per-worker connections
        ssh_factory = self._create_ssh_factory()

        self._worker_manager.add(
            Worker(
                worker_cfg,
                self._cfg,
                ssh_factory,
                shared_flap_state=shared_state,
                statistics=statistics,
            )
        )

    def _create_ssh_factory(self):
        """Create SSH connection factory for workers.

        Returns:
            Callable that creates new SSH connection
        """

        # Return factory that creates connection with same config as scanner
        # Subclasses can override to provide specific connection creation logic
        def factory():
            # Return a copy of the scanner's connection for now
            # This will be overridden in SutScanner
            return self._ssh

        return factory
