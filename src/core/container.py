"""Dependency injection container for loose coupling."""

from collections.abc import Callable
import logging
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}
        self._singletons: dict[str, Any] = {}

    def register_instance(self, service_type: type[T], instance: T) -> None:
        """Register a service instance."""
        key = self._get_key(service_type)
        self._services[key] = instance
        logger.debug(f"Registered instance: {key}")

    def register_factory(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for creating service instances."""
        key = self._get_key(service_type)
        self._factories[key] = factory
        logger.debug(f"Registered factory: {key}")

    def register_singleton(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """Register a singleton factory (created once, reused)."""
        key = self._get_key(service_type)
        self._factories[key] = factory
        self._singletons[key] = None  # Mark as singleton
        logger.debug(f"Registered singleton: {key}")

    def get(self, service_type: type[T]) -> T:
        """Get service instance."""
        key = self._get_key(service_type)

        # Check for direct instance
        if key in self._services:
            return self._services[key]

        # Check for singleton
        if key in self._singletons:
            if self._singletons[key] is None:
                self._singletons[key] = self._factories[key]()
            return self._singletons[key]

        # Check for factory
        if key in self._factories:
            return self._factories[key]()

        raise ValueError(f"Service not registered: {service_type}")

    def clear(self) -> None:
        """Clear all registrations."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.debug("Container cleared")

    def _get_key(self, service_type: type) -> str:
        """Get string key for service type."""
        return f"{service_type.__module__}.{service_type.__name__}"


# Global container instance
_container = Container()


def get_container() -> Container:
    """Get global container instance."""
    return _container
