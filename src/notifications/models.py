"""Notification data models."""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone


class NotificationStatus(Enum):
    """Status of notification delivery."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationTrigger(Enum):
    """Trigger type for notifications."""

    MANUAL_REFRESH = "manual_refresh"
    AUTO_REFRESH = "auto_refresh"
    ON_DEMAND = "on_demand"
    ERROR = "error"


@dataclass
class SlackNotification:
    """
    Slack notification message.

    Attributes:
        webhook_url: Slack webhook URL
        message: Formatted message payload
        trigger: What triggered this notification
        status: Delivery status
        timestamp: When notification was created
    """

    webhook_url: str
    message: dict
    trigger: NotificationTrigger
    status: NotificationStatus = NotificationStatus.PENDING
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
