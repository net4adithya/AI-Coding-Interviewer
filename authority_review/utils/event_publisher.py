import logging
from typing import Dict, Any, List
from ..interfaces.event_publisher_interface import EventPublisherInterface

logger = logging.getLogger("authority_review.events")

class InMemoryEventPublisher(EventPublisherInterface):
    """In-memory implementation of EventPublisherInterface.
    Stores published events in memory for inspection during testing/debugging
    and prepares the framework for future asynchronous message broker integration.
    """

    def __init__(self):
        self.published_events: List[Dict[str, Any]] = []

    def publish_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        record = {
            "event_name": event_name,
            "payload": payload,
        }
        self.published_events.append(record)
        logger.info(f"NOTIFICATION_EVENT_PUBLISHED: {record}")
