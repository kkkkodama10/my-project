# domain/entities.py

from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed: bool = False
    is_completed: bool = False
    
    def __post_init__(self):
        if not self.title:
            raise ValueError("Title cannot be empty")
