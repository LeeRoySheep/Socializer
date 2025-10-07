"""Data model for user life events."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LifeEventType(str, Enum):
    """Categories of life events."""
    BIRTH = "birth"
    EDUCATION = "education"
    CAREER = "career"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    LEGAL = "legal"
    TRAVEL = "travel"
    ACHIEVEMENT = "achievement"
    LOSS = "loss"
    OTHER = "other"

class LifeEvent(BaseModel):
    """Model representing a significant life event."""
    id: Optional[int] = None
    user_id: int
    event_type: LifeEventType
    title: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    people_involved: List[str] = Field(default_factory=list)
    impact_level: int = Field(ge=1, le=10, description="Importance of the event from 1-10")
    is_private: bool = True
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "event_type": "education",
                "title": "Graduated from University",
                "description": "Earned a Bachelor's degree in Computer Science",
                "start_date": "2020-05-15T00:00:00",
                "end_date": "2020-05-15T00:00:00",
                "location": "Stanford University, CA",
                "people_involved": [],
                "impact_level": 9,
                "is_private": False,
                "tags": ["education", "graduation", "computer_science"],
                "metadata": {"gpa": 3.8, "degree": "B.S. Computer Science"},
                "created_at": "2020-05-15T12:00:00",
                "updated_at": "2020-05-15T12:00:00"
            }
        }
