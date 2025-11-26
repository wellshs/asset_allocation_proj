"""Unit tests for rate limiter."""

import time


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_rate_limiter_creation(self):
        """Test creating a RateLimiter instance."""
        from src.account.rate_limiter import RateLimiter

        limiter = RateLimiter(delay=1.0)
        assert limiter.delay == 1.0

    def test_rate_limiter_enforces_delay(self):
        """Test that rate limiter enforces minimum delay between operations."""
        from src.account.rate_limiter import RateLimiter

        limiter = RateLimiter(delay=0.1)  # 100ms delay for testing

        # First operation should execute immediately
        start = time.time()
        with limiter:
            pass
        first_duration = time.time() - start
        assert first_duration < 0.05  # Should be nearly instant

        # Second operation should be delayed
        start = time.time()
        with limiter:
            pass
        second_duration = time.time() - start
        assert second_duration >= 0.1  # Should wait at least 100ms

    def test_rate_limiter_concurrent_requests(self):
        """Test rate limiter with multiple rapid requests."""
        from src.account.rate_limiter import RateLimiter

        limiter = RateLimiter(delay=0.05)  # 50ms delay

        operations = []
        for i in range(3):
            start = time.time()
            with limiter:
                operations.append(time.time() - start)

        # First operation should be fast
        assert operations[0] < 0.02
        # Subsequent operations should be delayed
        assert operations[1] >= 0.04
        assert operations[2] >= 0.04

    def test_rate_limiter_wait_method(self):
        """Test explicit wait() method."""
        from src.account.rate_limiter import RateLimiter

        limiter = RateLimiter(delay=0.1)

        # First wait should return quickly (no previous operation)
        start = time.time()
        limiter.wait()
        first_wait = time.time() - start
        assert first_wait < 0.05

        # Second wait should delay
        start = time.time()
        limiter.wait()
        second_wait = time.time() - start
        assert second_wait >= 0.1
