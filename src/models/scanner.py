"""Base scanner model."""

import logging
import threading

from src.core.connect import SshConnection
from src.core.enums.messages import LogMsg
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
        self._worker_manager.add(
            Worker(
                worker_cfg,
                self._cfg,
                self._ssh,
                shared_flap_state=shared_state,
                statistics=statistics,
            )
        )
