from abc import ABC, abstractmethod

class RateLimiterInterface(ABC):
    """Abstract rate limiter. Implementations must be safe for distributed environments."""

    @abstractmethod
    def is_allowed(self, key: str) -> bool:
        """Return True if the action is allowed for the given key, otherwise False."""
        ...

    @abstractmethod
    def record(self, key: str) -> None:
        """Record an occurrence for the given key (e.g., increment counter)."""
        ...
