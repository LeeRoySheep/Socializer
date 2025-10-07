"""Base class for chat agents."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Generic, Type
from datetime import datetime, timezone

from chat_agent.core.state import State

# Type variable for the state class to support different state implementations
StateT = TypeVar('StateT', bound=State)


class BaseAgent(ABC, Generic[StateT]):
    """Abstract base class for chat agents.
    
    This class defines the interface that all chat agents must implement.
    Concrete subclasses should implement the `process_message` method.
    """
    
    def __init__(
        self,
        state_class: Type[StateT] = State,  # type: ignore
        initial_state: Optional[StateT] = None,
        **kwargs
    ):
        """Initialize the agent.
        
        Args:
            state_class: The State class to use for managing conversation state.
            initial_state: Optional initial state to use. If not provided, a new state will be created.
            **kwargs: Additional keyword arguments to pass to the state constructor.
        """
        self.state_class = state_class
        self.state: StateT = initial_state if initial_state is not None else state_class(**kwargs)
    
    @abstractmethod
    async def process_message(
        self,
        message: str,
        sender: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a message and return a response.
        
        This method should be implemented by subclasses to define the agent's behavior.
        
        Args:
            message: The message text to process.
            sender: The sender of the message (e.g., 'user', 'assistant').
            metadata: Optional metadata to include with the message.
            **kwargs: Additional keyword arguments for message processing.
            
        Returns:
            A dictionary containing the response and any additional data.
        """
        pass
    
    def add_message(
        self,
        role: str,
        content: str,
        **kwargs
    ) -> None:
        """Add a message to the conversation history.
        
        Args:
            role: The role of the message sender (e.g., 'user', 'assistant').
            content: The message content.
            **kwargs: Additional message metadata.
        """
        self.state.add_message(role, content, **kwargs)
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update the conversation metadata.
        
        Args:
            updates: Dictionary of metadata updates to apply.
        """
        self.state.update_metadata(updates)
    
    def get_state(self) -> StateT:
        """Get the current conversation state.
        
        Returns:
            The current State object.
        """
        return self.state
    
    def set_state(self, state: StateT) -> None:
        """Set the conversation state.
        
        Args:
            state: The new state to use.
        """
        if not isinstance(state, self.state_class):
            raise ValueError(f"State must be an instance of {self.state_class.__name__}")
        self.state = state
    
    def reset(self, **kwargs) -> None:
        """Reset the agent's state.
        
        Args:
            **kwargs: Additional keyword arguments to pass to the state constructor.
        """
        self.state = self.state_class(**kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the agent's state to a dictionary.
        
        Returns:
            A dictionary representation of the agent's state.
        """
        return {
            "state": self.state.to_dict(),
            "state_class": self.state_class.__name__,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        state_class_map: Optional[Dict[str, Type[State]]] = None
    ) -> 'BaseAgent[StateT]':
        """Create an agent from a dictionary representation.
        
        Args:
            data: Dictionary containing the agent's state.
            state_class_map: Optional mapping of state class names to state classes.
                            If not provided, only the default State class will be used.
                            
        Returns:
            A new agent instance with the deserialized state.
            
        Raises:
            ValueError: If the state class is not found in the state_class_map.
        """
        state_class_name = data.get("state_class", "State")
        
        # Default to the base State class if no mapping is provided
        if not state_class_map:
            state_class_map = {"State": State}
        
        if state_class_name not in state_class_map:
            raise ValueError(f"Unknown state class: {state_class_name}")
        
        state_class = state_class_map[state_class_name]
        state = state_class.from_dict(data["state"])
        
        return cls(state_class=state_class, initial_state=state)
