"""
Life Event Tool with OTE Compliance

LOCATION: tools/events/life_event_tool.py
PURPOSE: Manage user life events (birthdays, graduations, job changes, etc.) with OTE tracking

TRACE POINTS:
    - VALIDATE: Input validation
    - ADD: Add new event
    - GET: Retrieve event
    - UPDATE: Update event
    - DELETE: Delete event
    - LIST: List events
    - TIMELINE: Generate timeline

DEPENDENCIES:
    - datamanager.DataManager
    - datamanager.life_event_manager.LifeEventManager
    
OTE COMPLIANCE:
    - Observability: All CRUD operations logged with timing
    - Traceability: Trace markers for each operation type
    - Evaluation: Operation success rates, performance metrics
"""

from datetime import datetime
from typing import Type, Any, Dict, List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, field_validator

from datamanager.data_manager import DataManager
from datamanager.life_event_manager import LifeEventManager
from app.utils import get_logger, observe, traceable, evaluate

# Get logger for this module
logger = get_logger(__name__)


class LifeEventInput(BaseModel):
    """
    Input schema for LifeEventTool.
    
    Attributes:
        action: Action to perform (add, get, update, delete, list, timeline)
        user_id: ID of the user
        event_id: ID of the event (for get, update, delete)
        event_type: Type of event (BIRTHDAY, GRADUATION, JOB_CHANGE, etc.)
        title: Event title
        description: Detailed description
        start_date: When event started (YYYY-MM-DD)
        end_date: When event ended (YYYY-MM-DD)
        location: Where event occurred
        impact_level: Importance level 1-10
        is_private: Whether event is private (default: True)
        limit: Maximum events to return (default: 50)
        offset: Offset for pagination (default: 0)
    """
    action: str = Field(description="Action to perform: add, get, update, delete, list, timeline")
    user_id: int = Field(description="ID of the user")
    event_id: Optional[int] = Field(default=None, description="ID of the event")
    event_type: Optional[str] = Field(default=None, description="Type of the event")
    title: Optional[str] = Field(default=None, description="Title of the event")
    description: Optional[str] = Field(default=None, description="Detailed description")
    start_date: Optional[str] = Field(default=None, description="When event started YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="When event ended YYYY-MM-DD")
    location: Optional[str] = Field(default=None, description="Where event occurred")
    impact_level: Optional[int] = Field(default=None, description="Importance level 1-10")
    is_private: Optional[bool] = Field(default=True, description="Whether event is private")
    limit: Optional[int] = Field(default=50, description="Maximum events to return")
    offset: Optional[int] = Field(default=0, description="Offset for pagination")

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_dates(cls, v):
        """Parse date strings into datetime objects."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except (ValueError, TypeError):
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
        return v


class LifeEventTool(BaseTool):
    """
    Tool for managing user life events with OTE tracking.
    
    This tool provides CRUD operations for tracking significant life events
    like birthdays, graduations, job changes, and other milestones. All
    operations are logged and timed for performance monitoring.
    
    OTE Compliance:
        - All operations observed with timing
        - Trace markers show CRUD flow
        - Success/failure rates tracked per operation
        - Event counts and timeline metrics
    
    Attributes:
        name: Tool name for LLM
        description: Tool description for LLM
        args_schema: Pydantic schema for validation
        dm: DataManager instance
        event_manager: LifeEventManager for event operations
    
    Example:
        >>> tool = LifeEventTool(data_manager)
        >>> result = tool.run({
        ...     "action": "add",
        ...     "user_id": 123,
        ...     "event_type": "BIRTHDAY",
        ...     "title": "30th Birthday",
        ...     "start_date": "2024-11-12"
        ... })
        >>> print(result["status"])
        success
    """
    
    name: str = "life_event"
    description: str = """
    Manage and track important life events for users. 
    Use this tool to record significant life events like birthdays, graduations, job changes, etc.
    """
    args_schema: Type[BaseModel] = LifeEventInput
    dm: Any = None
    event_manager: Any = None
    
    def __init__(self, data_manager: DataManager, **kwargs):
        """
        Initialize LifeEventTool with event manager.
        
        Args:
            data_manager: DataManager instance for database operations
            **kwargs: Additional Pydantic model data
        """
        super().__init__(**kwargs)
        self.dm = data_manager
        
        logger.trace("INIT", "Initializing LifeEventManager")
        object.__setattr__(self, 'event_manager', LifeEventManager(data_manager))
        
        logger.observe("init_complete", has_event_manager=bool(self.event_manager))
    
    @observe("life_event_run")
    @evaluate(detect_anomalies=True)
    def _run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute life event tool synchronously with OTE tracking.
        
        TRACE PATH:
            VALIDATE → Action-specific path
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments with action and event data
            
        Returns:
            Dictionary with operation result
        """
        return self._handle_event(kwargs)
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute life event tool asynchronously.
        
        Note:
            Currently calls sync version. Can be optimized for async DB operations.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Dictionary with operation result
        """
        return self._handle_event(kwargs)
    
    @traceable()
    def _handle_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to appropriate handler based on action.
        
        TRACE PATH:
            VALIDATE → Route to handler → Execute
        
        Args:
            data: Event data with action and parameters
            
        Returns:
            Dictionary with operation result
        """
        action = data.get('action', '').lower()
        user_id = data.get('user_id')
        
        # TRACE POINT: Validation
        logger.trace("VALIDATE", f"Validating action={action}, user_id={user_id}")
        
        if not user_id:
            logger.warning("Validation failed: missing user_id")
            return {"status": "error", "message": "User ID is required"}
        
        try:
            # Route to appropriate handler
            if action == 'add':
                return self._add_event(user_id, data)
            elif action == 'get':
                return self._get_event(user_id, data.get('event_id'))
            elif action == 'update':
                return self._update_event(user_id, data)
            elif action == 'delete':
                return self._delete_event(user_id, data.get('event_id'))
            elif action == 'list':
                return self._list_events(user_id, data)
            elif action == 'timeline':
                return self._get_timeline(user_id)
            else:
                logger.warning(f"Unknown action: {action}")
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in life event tool: {str(e)}", exc_info=True)
            return {"status": "error", "message": f"Error in life event tool: {str(e)}"}
    
    @traceable()
    @observe("add_event")
    def _add_event(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new life event.
        
        TRACE PATH:
            ADD → Prepare data → Save to DB
        
        Args:
            user_id: User ID
            data: Event data
            
        Returns:
            Dictionary with added event or error
        """
        logger.trace("ADD", f"Adding event for user={user_id}, type={data.get('event_type')}")
        
        event_data = {
            "user_id": user_id,
            "event_type": data.get('event_type', 'OTHER'),
            "title": data.get('title', 'Untitled Event'),
            "description": data.get('description', ''),
            "start_date": data.get('start_date', datetime.utcnow()),
            "end_date": data.get('end_date'),
            "location": data.get('location'),
            "people_involved": data.get('people_involved', []),
            "impact_level": data.get('impact_level', 5),
            "is_private": data.get('is_private', True),
            "tags": data.get('tags', []),
            "metadata": data.get('metadata', {})
        }
        
        event = self.event_manager.add_event(event_data)
        
        if event:
            logger.observe("add_complete", success=True, event_type=event_data['event_type'])
            return {
                "status": "success",
                "message": "Life event added successfully",
                "event": event.dict()
            }
        else:
            logger.observe("add_complete", success=False)
            return {
                "status": "error",
                "message": "Failed to add event"
            }
    
    @traceable()
    @observe("get_event")
    def _get_event(self, user_id: int, event_id: Optional[int]) -> Dict[str, Any]:
        """
        Get a specific event.
        
        TRACE PATH:
            GET → Validate ID → Retrieve from DB
        
        Args:
            user_id: User ID
            event_id: Event ID to retrieve
            
        Returns:
            Dictionary with event or error
        """
        logger.trace("GET", f"Getting event_id={event_id} for user={user_id}")
        
        if not event_id:
            logger.warning("GET failed: missing event_id")
            return {"status": "error", "message": "Event ID is required"}
        
        event = self.event_manager.get_event(event_id, user_id)
        
        if not event:
            logger.observe("get_complete", success=False, found=False)
            return {"status": "error", "message": "Event not found"}
        
        logger.observe("get_complete", success=True, found=True)
        return {
            "status": "success",
            "event": event.dict()
        }
    
    @traceable()
    @observe("update_event")
    def _update_event(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing event.
        
        TRACE PATH:
            UPDATE → Validate → Prepare data → Update DB
        
        Args:
            user_id: User ID
            data: Update data
            
        Returns:
            Dictionary with updated event or error
        """
        event_id = data.get('event_id')
        
        logger.trace("UPDATE", f"Updating event_id={event_id} for user={user_id}")
        
        if not event_id:
            logger.warning("UPDATE failed: missing event_id")
            return {"status": "error", "message": "Event ID is required for update"}
        
        # Remove None values and action/event_id from update data
        update_data = {k: v for k, v in data.items() 
                      if v is not None and k not in ('action', 'event_id')}
        
        if not update_data:
            logger.warning("UPDATE failed: no data provided")
            return {"status": "error", "message": "No update data provided"}
        
        event = self.event_manager.update_event(event_id, user_id, update_data)
        
        if not event:
            logger.observe("update_complete", success=False)
            return {"status": "error", "message": "Failed to update event"}
        
        logger.observe("update_complete", success=True, fields_updated=len(update_data))
        return {
            "status": "success",
            "message": "Event updated successfully",
            "event": event.dict()
        }
    
    @traceable()
    @observe("delete_event")
    def _delete_event(self, user_id: int, event_id: Optional[int]) -> Dict[str, Any]:
        """
        Delete an event.
        
        TRACE PATH:
            DELETE → Validate ID → Delete from DB
        
        Args:
            user_id: User ID
            event_id: Event ID to delete
            
        Returns:
            Dictionary with success or error
        """
        logger.trace("DELETE", f"Deleting event_id={event_id} for user={user_id}")
        
        if not event_id:
            logger.warning("DELETE failed: missing event_id")
            return {"status": "error", "message": "Event ID is required"}
        
        success = self.event_manager.delete_event(event_id, user_id)
        
        if not success:
            logger.observe("delete_complete", success=False)
            return {"status": "error", "message": "Failed to delete event"}
        
        logger.observe("delete_complete", success=True)
        return {
            "status": "success",
            "message": "Event deleted successfully"
        }
    
    @traceable()
    @observe("list_events")
    def _list_events(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List events with optional filtering.
        
        TRACE PATH:
            LIST → Apply filters → Retrieve from DB
        
        Args:
            user_id: User ID
            data: Filter parameters (event_type, limit, offset)
            
        Returns:
            Dictionary with list of events
        """
        event_type = data.get('event_type')
        limit = data.get('limit', 50)
        offset = data.get('offset', 0)
        
        logger.trace("LIST", f"Listing events for user={user_id}, type={event_type}, limit={limit}")
        
        events = self.event_manager.get_user_events(
            user_id=user_id,
            event_type=event_type,
            limit=limit,
            offset=offset
        )
        
        logger.observe("list_complete", count=len(events), success=True)
        
        return {
            "status": "success",
            "count": len(events),
            "events": [e.dict() for e in events]
        }
    
    @traceable()
    @observe("get_timeline")
    def _get_timeline(self, user_id: int) -> Dict[str, Any]:
        """
        Get a timeline of events grouped by year.
        
        TRACE PATH:
            TIMELINE → Retrieve all events → Group by year
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with timeline grouped by year
        """
        logger.trace("TIMELINE", f"Generating timeline for user={user_id}")
        
        timeline = self.event_manager.get_timeline(user_id)
        
        # Convert Pydantic models to dicts for JSON serialization
        timeline_dict = {
            str(year): [e.dict() for e in events] 
            for year, events in timeline.items()
        }
        
        total_events = sum(len(events) for events in timeline.values())
        logger.observe("timeline_complete", years=len(timeline), total_events=total_events, success=True)
        
        return {
            "status": "success",
            "timeline": timeline_dict
        }
