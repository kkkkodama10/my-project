from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class PersonResponse(BaseModel):
    id: str
    name: str
    image_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonListResponse(BaseModel):
    id: str
    name: str
    image_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
