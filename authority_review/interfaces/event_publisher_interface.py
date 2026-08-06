from abc import ABC, abstractmethod
from typing import Dict, Any

class EventPublisherInterface(ABC):
    @abstractmethod
    def publish_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Publish a domain event asynchronously or in-memory."""
        raise NotImplementedError
