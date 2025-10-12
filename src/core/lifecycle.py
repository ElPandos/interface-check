"""Component lifecycle management for proper resource cleanup."""

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class ILifecycleAware(ABC):
    """Interface for components that need lifecycle management."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize component resources."""

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up component resources."""


class LifecycleManager:
    """Manages component lifecycle and ensures proper cleanup."""

    def __init__(self):
        self._components: list[ILifecycleAware] = []
        self._initialized = False

    def register(self, component: ILifecycleAware) -> None:
        """Register component for lifecycle management."""
        self._components.append(component)
        if self._initialized:
            component.initialize()
        logger.debug(f"Registered component: {type(component).__name__}")

    def initialize_all(self) -> None:
        """Initialize all registered components."""
        for component in self._components:
            try:
                component.initialize()
                logger.debug(f"Initialized: {type(component).__name__}")
            except Exception:
                logger.exception(f"Failed to initialize: {type(component).__name__}")
        self._initialized = True

    def cleanup_all(self) -> None:
        """Clean up all registered components in reverse order."""
        for component in reversed(self._components):
            try:
                component.cleanup()
                logger.debug(f"Cleaned up: {type(component).__name__}")
            except Exception:
                logger.exception(f"Failed to cleanup: {type(component).__name__}")
        self._initialized = False

    @contextmanager
    def managed_lifecycle(self) -> Generator[None]:
        """Context manager for automatic lifecycle management."""
        try:
            self.initialize_all()
            yield
        finally:
            self.cleanup_all()

    def clear(self) -> None:
        """Clear all registered components."""
        self.cleanup_all()
        self._components.clear()
        logger.debug("Lifecycle manager cleared")
