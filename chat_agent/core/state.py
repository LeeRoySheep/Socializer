"""Core state management for chat agent conversations."""
from datetime import datetime, timezone
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class State:
    """Manages the state of a conversation, including messages and metadata."""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        now = datetime.now(timezone.utc)
        if not hasattr(self, 'created_at') or not self.created_at:
            self.created_at = now
        if not hasattr(self, 'updated_at') or not self.updated_at:
            self.updated_at = now

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add a message to the conversation."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)

    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update the metadata dictionary with new key-value pairs."""
        self.metadata.update(updates)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the state to a dictionary."""
        return {
            "messages": self.messages,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'State':
        """Create a State instance from a dictionary."""
        data = data.copy()
        
        # Handle datetime conversion
        datetime_fields = ['created_at', 'updated_at']
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                # Convert string to datetime and ensure it's timezone-aware
                dt = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                data[field] = dt
        
        # Handle messages timestamps
        if 'messages' in data and data['messages']:
            for msg in data['messages']:
                if 'timestamp' in msg and isinstance(msg['timestamp'], str):
                    # Convert string to datetime and ensure it's timezone-aware
                    dt = datetime.fromisoformat(
                        msg['timestamp'].replace('Z', '+00:00')
                    )
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    msg['timestamp'] = dt
        
        return cls(**data)

    def __eq__(self, other: object) -> bool:
        """Compare two State instances for equality.

        Two states are considered equal if they have the same messages and metadata.
        Timestamps are not considered in the comparison.
        """
        if not isinstance(other, State):
            return False
        return (self.messages == other.messages and
                self.metadata == other.metadata)

    def __repr__(self) -> str:
        """Return a string representation of the State."""
        return (f"State(messages={len(self.messages)} messages, "
                f"metadata={len(self.metadata)} items, "
                f"created_at={self.created_at.isoformat()}, "
                f"updated_at={self.updated_at.isoformat()})")