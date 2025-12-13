"""Rate limiter for API request throttling."""

import time
import threading
from typing import Optional


class RateLimiter:
    """
    Rate limiter to ensure minimum delay between operations.

    Uses a simple time-based approach to enforce rate limits by tracking
    the last operation time and waiting if necessary.

    Attributes:
        delay: Minimum seconds between operations
    """

    def __init__(self, delay: float):
        """
        Initialize rate limiter.

        Args:
            delay: Minimum seconds to wait between operations
        """
        self.delay = delay
        self._last_operation: Optional[float] = None
        self._lock = threading.Lock()

    def wait(self) -> None:
        """
        Wait if necessary to enforce rate limit.

        Calculates time since last operation and sleeps if needed
        to maintain the configured delay between operations.
        """
        with self._lock:
            if self._last_operation is not None:
                elapsed = time.time() - self._last_operation
                if elapsed < self.delay:
                    sleep_time = self.delay - elapsed
                    time.sleep(sleep_time)
            self._last_operation = time.time()

    def __enter__(self):
        """Context manager entry - enforces rate limit."""
        self.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False
