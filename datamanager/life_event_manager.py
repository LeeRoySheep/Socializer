"""Life event management for user profiles."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from models.life_event import LifeEvent, LifeEventType
from datamanager.data_model import Base  # Use the same Base as other models

class LifeEventModel(Base):
    """SQLAlchemy model for life events."""
    __tablename__ = 'life_events'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    event_type = Column(SQLEnum(LifeEventType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(2000))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    location = Column(String(500), nullable=True)
    people_involved = Column(JSON, default=list)
    impact_level = Column(Integer, default=5)
    is_private = Column(Boolean, default=True)
    tags = Column(JSON, default=list)
    # Renamed to avoid conflict with SQLAlchemy's metadata
    event_metadata = Column('metadata', JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Convert 'metadata' to 'event_metadata' if present
        if 'metadata' in kwargs:
            kwargs['event_metadata'] = kwargs.pop('metadata')
        super().__init__(**kwargs)

class LifeEventManager:
    """Manager for user life events."""
    
    def __init__(self, data_manager):
        """Initialize with a DataManager or DataModel instance."""
        self.data_manager = data_manager
        # Check if data_manager has a data_model attribute (DataManager) or is a DataModel
        if hasattr(data_manager, 'data_model'):
            self.data_model = data_manager.data_model
        else:
            self.data_model = data_manager
        self.db = next(self.data_model.get_db())
    
    def add_event(self, event_data: Dict[str, Any]) -> LifeEvent:
        """Add a new life event."""
        # Create a copy to avoid modifying the original dictionary
        event_data = event_data.copy()
        
        # Convert date strings to datetime objects if needed
        if 'start_date' in event_data and isinstance(event_data['start_date'], str):
            event_data['start_date'] = datetime.fromisoformat(event_data['start_date'])
            
        if 'end_date' in event_data and event_data['end_date'] and isinstance(event_data['end_date'], str):
            event_data['end_date'] = datetime.fromisoformat(event_data['end_date'])
        
        try:
            event = LifeEventModel(**event_data)
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return self._to_pydantic(event)
        except Exception as e:
            self.db.rollback()
            raise
    
    def get_event(self, event_id: int, user_id: int) -> Optional[LifeEvent]:
        """Get a specific event by ID."""
        event = self.db.query(LifeEventModel).filter(
            LifeEventModel.id == event_id,
            LifeEventModel.user_id == user_id
        ).first()
        return self._to_pydantic(event) if event else None
    
    def get_user_events(
        self, 
        user_id: int,
        event_type: Optional[LifeEventType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[LifeEvent]:
        """Get events for a user with optional filtering."""
        query = self.db.query(LifeEventModel).filter(
            LifeEventModel.user_id == user_id
        )
        
        if event_type:
            query = query.filter(LifeEventModel.event_type == event_type)
            
        events = query.order_by(
            LifeEventModel.start_date.desc()
        ).offset(offset).limit(limit).all()
        
        return [self._to_pydantic(e) for e in events]
    
    def update_event(
        self, 
        event_id: int, 
        user_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[LifeEvent]:
        """Update an existing event."""
        event = self.db.query(LifeEventModel).filter(
            LifeEventModel.id == event_id,
            LifeEventModel.user_id == user_id
        ).first()
        
        if not event:
            return None
            
        for key, value in update_data.items():
            setattr(event, key, value)
            
        event.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(event)
        return self._to_pydantic(event)
    
    def delete_event(self, event_id: int, user_id: int) -> bool:
        """Delete an event."""
        event = self.db.query(LifeEventModel).filter(
            LifeEventModel.id == event_id,
            LifeEventModel.user_id == user_id
        ).first()
        
        if not event:
            return False
            
        self.db.delete(event)
        self.db.commit()
        return True
    
    def get_timeline(self, user_id: int) -> Dict[str, List[LifeEvent]]:
        """Get a timeline of events grouped by year."""
        events = self.get_user_events(user_id, limit=1000)  # Get all events
        timeline = {}
        
        for event in events:
            year = event.start_date.year
            if year not in timeline:
                timeline[year] = []
            timeline[year].append(event)
            
        # Sort years in descending order
        return {year: timeline[year] for year in sorted(timeline.keys(), reverse=True)}
    
    @staticmethod
    def _to_pydantic(event: LifeEventModel) -> LifeEvent:
        """Convert SQLAlchemy model to Pydantic model."""
        if not event:
            return None
            
        # Convert SQLAlchemy model to dictionary
        event_dict = {
            'id': event.id,
            'user_id': event.user_id,
            'event_type': event.event_type,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'location': event.location,
            'people_involved': event.people_involved or [],
            'impact_level': event.impact_level,
            'is_private': event.is_private,
            'tags': event.tags or [],
            'metadata': event.event_metadata or {},
            'created_at': event.created_at,
            'updated_at': event.updated_at
        }
        
        # Create and return the Pydantic model
        return LifeEvent(**event_dict)
