from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileBase(BaseModel):
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None

class FileCreate(FileBase):
    pass

class FileUpdate(BaseModel):
    content_summary: Optional[str] = None
    parsed_content: Optional[str] = None

class FileResponse(FileBase):
    id: int
    content_summary: Optional[str] = None
    parsed_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
