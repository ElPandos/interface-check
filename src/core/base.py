"""Base classes for improved independence and reusability."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass(frozen=True)
class Result[T]:
    """Generic result wrapper for operations."""

    success: bool
    data: T | None = None
    error: str | None = None

    @classmethod
    def ok(cls, data: T) -> Result[T]:
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> Result[T]:
        return cls(success=False, error=error)


class Component(ABC):
    """Base component with lifecycle management."""

    def __init__(self, name: str):
        self._name = name
        self._initialized = False
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> Result[None]:
        """Initialize component."""
        try:
            self._do_initialize()
            self._initialized = True
            return Result.ok(None)
        except Exception as e:
            self._logger.exception(f"Failed to initialize {self._name}")
            return Result.fail(str(e))

    def cleanup(self) -> Result[None]:
        """Cleanup component resources."""
        try:
            self._do_cleanup()
            self._initialized = False
            return Result.ok(None)
        except Exception as e:
            self._logger.exception(f"Failed to cleanup {self._name}")
            return Result.fail(str(e))

    @abstractmethod
    def _do_initialize(self) -> None:
        """Override to implement initialization logic."""

    @abstractmethod
    def _do_cleanup(self) -> None:
        """Override to implement cleanup logic."""


class Service(Component):
    """Base service class with dependency injection."""

    def __init__(self, name: str, dependencies: list[Component] | None = None):
        super().__init__(name)
        self._dependencies = dependencies or []

    def add_dependency(self, component: Component) -> None:
        """Add dependency component."""
        self._dependencies.append(component)

    def initialize(self) -> Result[None]:
        """Initialize service and dependencies."""
        # Initialize dependencies first
        for dep in self._dependencies:
            if not dep.initialized:
                result = dep.initialize()
                if not result.success:
                    return Result.fail(f"Failed to initialize dependency {dep.name}: {result.error}")

        return super().initialize()


class Repository(Generic[T], ABC):
    """Base repository pattern for data access."""

    @abstractmethod
    def find_by_id(self, id: str) -> T | None:
        """Find entity by ID."""

    @abstractmethod
    def find_all(self) -> list[T]:
        """Find all entities."""

    @abstractmethod
    def save(self, entity: T) -> Result[T]:
        """Save entity."""

    @abstractmethod
    def delete(self, id: str) -> Result[None]:
        """Delete entity by ID."""


class Factory(Generic[T], ABC):
    """Base factory pattern."""

    @abstractmethod
    def create(self, **kwargs) -> T:
        """Create instance."""


class Observer(ABC):
    """Observer pattern interface."""

    @abstractmethod
    def update(self, event: Any) -> None:
        """Handle event update."""


class Subject:
    """Subject for observer pattern."""

    def __init__(self):
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        """Attach observer."""
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Detach observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: Any) -> None:
        """Notify all observers."""
        for observer in self._observers:
            try:
                observer.update(event)
            except Exception as e:
                logger.exception(f"Observer {observer} failed to handle event: {e}")


class Validator(Generic[T], ABC):
    """Base validator interface."""

    @abstractmethod
    def validate(self, data: T) -> Result[None]:
        """Validate data."""


class Cache(Generic[T], ABC):
    """Base cache interface."""

    @abstractmethod
    def get(self, key: str) -> T | None:
        """Get cached value."""

    @abstractmethod
    def put(self, key: str, value: T, ttl: int | None = None) -> None:
        """Put value in cache."""

    @abstractmethod
    def remove(self, key: str) -> None:
        """Remove from cache."""

    @abstractmethod
    def clear(self) -> None:
        """Clear cache."""


class SimpleCache(Cache[T]):
    """Simple in-memory cache implementation."""

    def __init__(self):
        self._data: dict[str, T] = {}

    def get(self, key: str) -> T | None:
        return self._data.get(key)

    def put(self, key: str, value: T, _ttl: int | None = None) -> None:
        self._data[key] = value

    def remove(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()
