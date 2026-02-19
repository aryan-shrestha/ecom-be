"""System clock implementation."""

from datetime import datetime, timezone

from app.application.ports.clock_port import ClockPort


class SystemClock(ClockPort):
    """Real system clock implementation."""

    def now(self) -> datetime:
        """Get current UTC datetime (naive, for consistency with DB)."""
        return datetime.now(timezone.utc).replace(tzinfo=None)
