"""Clock port for time-dependent operations (enables deterministic testing)."""

from abc import ABC, abstractmethod
from datetime import datetime


class ClockPort(ABC):
    """Port interface for clock operations."""

    @abstractmethod
    def now(self) -> datetime:
        """Get current datetime (UTC)."""
        ...
