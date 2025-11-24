"""Slack integration for notifications."""

import requests

from src.notifications.models import SlackNotification, NotificationStatus


class SlackClient:
    """Client for sending Slack notifications."""

    def __init__(self, webhook_url: str, timeout: int = 5):
        """
        Initialize Slack client.

        Args:
            webhook_url: Slack webhook URL
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send(self, notification: SlackNotification) -> bool:
        """
        Send notification to Slack.

        Args:
            notification: Notification to send

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            response = requests.post(
                notification.webhook_url,
                json=notification.message,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                notification.status = NotificationStatus.SENT
                return True
            else:
                notification.status = NotificationStatus.FAILED
                print(f"Slack webhook failed: {response.status_code} - {response.text}")
                return False

        except requests.Timeout:
            notification.status = NotificationStatus.FAILED
            print("Slack webhook timeout")
            return False
        except requests.RequestException as e:
            notification.status = NotificationStatus.FAILED
            print(f"Slack webhook error: {e}")
            return False
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            print(f"Unexpected error sending Slack notification: {e}")
            return False

    @staticmethod
    def validate_webhook_url(url: str) -> bool:
        """
        Validate Slack webhook URL format.

        Args:
            url: URL to validate

        Returns:
            bool: True if URL format is valid
        """
        return url.startswith("https://hooks.slack.com/services/")


def send_portfolio_update(
    holdings,
    webhook_url: str,
    format_type: str = "detailed",
    trigger_type: str = "manual_refresh",
) -> bool:
    """
    Send portfolio update to Slack.

    Args:
        holdings: AccountHoldings to send
        webhook_url: Slack webhook URL
        format_type: "detailed" or "summary"
        trigger_type: Notification trigger

    Returns:
        bool: True if sent successfully
    """
    from src.notifications.formatters import PortfolioFormatter
    from src.notifications.models import NotificationTrigger

    # Validate webhook URL
    if not SlackClient.validate_webhook_url(webhook_url):
        print(f"Invalid Slack webhook URL: {webhook_url}")
        return False

    # Format message
    formatter = PortfolioFormatter()
    if format_type == "summary":
        message = formatter.format_summary(holdings)
    else:
        message = formatter.format_detailed(holdings)

    # Create notification
    trigger = NotificationTrigger(trigger_type)
    notification = SlackNotification(
        webhook_url=webhook_url, message=message, trigger=trigger
    )

    # Send
    client = SlackClient(webhook_url)
    return client.send(notification)
