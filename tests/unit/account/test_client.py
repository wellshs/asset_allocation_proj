"""Unit tests for client retry logic."""

import pytest
from unittest.mock import Mock


class TestExponentialBackoffRetry:
    """Test exponential backoff retry decorator."""

    def test_retry_on_transient_failure(self):
        """Test that transient failures are retried."""
        from src.account.client import with_retry
        from src.account.exceptions import AccountAPIException

        # Create a function that fails twice then succeeds
        mock_func = Mock(
            side_effect=[
                AccountAPIException("Temporary error"),
                AccountAPIException("Another temporary error"),
                "success",
            ]
        )

        @with_retry
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_exhaustion_raises_exception(self):
        """Test that retry exhaustion raises the last exception."""
        from src.account.client import with_retry
        from src.account.exceptions import AccountAPIException

        # Create a function that always fails
        mock_func = Mock(side_effect=AccountAPIException("Permanent error"))

        @with_retry
        def test_func():
            return mock_func()

        with pytest.raises(AccountAPIException):
            test_func()

        # Should try 3 times (initial + 2 retries) based on plan.md
        assert mock_func.call_count == 3

    def test_no_retry_on_auth_error(self):
        """Test that authentication errors are not retried."""
        from src.account.client import with_retry
        from src.account.exceptions import AccountAuthException

        mock_func = Mock(side_effect=AccountAuthException("Invalid credentials"))

        @with_retry
        def test_func():
            return mock_func()

        with pytest.raises(AccountAuthException):
            test_func()

        # Should not retry auth errors
        assert mock_func.call_count == 1

    def test_successful_first_attempt_no_retry(self):
        """Test that successful calls don't trigger retries."""
        from src.account.client import with_retry

        mock_func = Mock(return_value="success")

        @with_retry
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1
