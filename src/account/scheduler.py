"""Scheduler for automatic periodic refresh."""

import threading
from typing import Optional, Callable
from src.account.logging import logger


class Scheduler:
    """Scheduler for periodic account data refresh."""

    def __init__(self, interval_minutes: int, callback: Callable):
        """
        Initialize scheduler.

        Args:
            interval_minutes: Minutes between refreshes
            callback: Function to call on each refresh
        """
        self.interval_minutes = interval_minutes
        self.callback = callback
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start the scheduler in a background thread."""
        if self._thread and self._thread.is_alive():
            logger.info("Scheduler already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Scheduler started (interval: {self.interval_minutes} minutes)")

    def stop(self):
        """Stop the scheduler gracefully."""
        if not self._thread or not self._thread.is_alive():
            logger.info("Scheduler not running")
            return

        self._stop_event.set()
        self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _run(self):
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            try:
                # Execute callback
                self._run_scheduled_fetch()

                # Wait for next interval
                self._stop_event.wait(timeout=self.interval_minutes * 60)

            except Exception as e:
                logger.error(f"Error in scheduled refresh: {e}")
                # Continue running despite errors
                self._stop_event.wait(timeout=60)  # Wait 1 minute before retrying

    def _run_scheduled_fetch(self):
        """Execute the scheduled fetch."""
        try:
            self.callback()
        except Exception as e:
            logger.error(f"Scheduled fetch failed: {e}")
            # Don't re-raise - log and continue


def create_auto_refresh_scheduler(service, config) -> Optional[Scheduler]:
    """
    Create auto-refresh scheduler from configuration.

    Args:
        service: AccountService instance
        config: Configuration object

    Returns:
        Scheduler instance if auto-refresh is enabled, None otherwise
    """
    if not config.refresh.auto_enabled:
        return None

    def refresh_callback():
        """Callback for scheduled refresh."""
        logger.info("Auto-refresh triggered")

        try:
            all_holdings = service.get_all_holdings()

            # Send Slack notifications if configured
            if config.notifications.slack.enabled:
                if "auto_refresh" in config.notifications.slack.triggers:
                    from src.notifications.slack import send_portfolio_update

                    for name, holdings in all_holdings.items():
                        send_portfolio_update(
                            holdings,
                            config.notifications.slack.webhook_url,
                            config.notifications.slack.format,
                            "auto_refresh",
                        )

            logger.info(f"Auto-refresh completed: {len(all_holdings)} accounts")

        except Exception as e:
            logger.error(f"Auto-refresh error: {e}")

    scheduler = Scheduler(
        interval_minutes=config.refresh.interval_minutes, callback=refresh_callback
    )

    return scheduler
