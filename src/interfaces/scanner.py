"""Scanner interface definition."""

from abc import ABC, abstractmethod

from src.core.worker import WorkManager


class IScanner(ABC):
    """Interface for scanner implementations."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to target system.

        Returns:
            bool: True if successful
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect and clean up resources."""

    @abstractmethod
    def run(self) -> None:
        """Run scanner operations."""

    @property
    @abstractmethod
    def worker_manager(self) -> WorkManager:
        """Get worker manager.

        Returns:
            WorkManager: Worker manager instance
        """
