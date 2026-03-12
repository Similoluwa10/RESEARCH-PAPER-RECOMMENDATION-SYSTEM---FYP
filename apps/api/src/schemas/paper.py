"""
Paper Schemas

Pydantic models for paper request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaperBase(BaseModel):
    """Base paper schema."""
    
    title: str = Field(..., min_length=1, max_length=500)
    abstract: str = Field(..., min_length=10)
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = Field(None, ge=1990, le=2100)
    venue: Optional[str] = Field(None, max_length=200)
    keywords: List[str] = Field(default_factory=list)
    doi: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    category: str = Field(default="Other", max_length=100)
    source: str = Field(default="Other", max_length=50)


class PaperCreate(PaperBase):
    """Schema for creating a paper."""
    pass


class PaperUpdate(BaseModel):
    """Schema for updating a paper."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    abstract: Optional[str] = Field(None, min_length=10)
    authors: Optional[List[str]] = None
    year: Optional[int] = Field(None, ge=1990, le=2100)
    venue: Optional[str] = Field(None, max_length=200)
    keywords: Optional[List[str]] = None
    doi: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=50)
    


class PaperResponse(PaperBase):
    """Schema for paper response."""
    
    id: UUID    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaperList(BaseModel):
    """Schema for paginated paper list."""
    
    papers: List[PaperResponse]
    total: int
    page: int
    page_size: int


# Alias for backwards compatibility
PaperListResponse = PaperList
