"""
base.py - Base API Client

Abstract base class for all external API clients.
Provides common functionality and defines the interface.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class PaperData:
    """
    Standard paper data structure returned by all API clients.
    
    This dataclass normalizes paper data from different APIs
    into a consistent format for processing.
    """
    
    title: str
    abstract: str
    authors: List[str]
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    venue: Optional[str] = None
    source: str = "unknown"
    date_fetched: datetime = field(default_factory=datetime.utcnow)
    
    def __repr__(self) -> str:
        title_preview = self.title[:50] if len(self.title) > 50 else self.title
        return f"<PaperData(title='{title_preview}...', source='{self.source}')>"


class LoggerMixin:
    """Mixin class to add logging capability."""
    
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)


class BaseAPIClient(ABC, LoggerMixin):
    """
    Abstract base class for all API clients.
    
    All API clients should inherit from this class and
    implement the required abstract methods.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Get the API source name."""
        pass
    
    @abstractmethod
    def search(self, query: str, max_results: int = 100) -> List[PaperData]:
        """
        Search for papers using the API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of PaperData objects
        """
        pass
    
    @abstractmethod
    def get_paper(self, paper_id: str) -> Optional[PaperData]:
        """
        Get details for a specific paper by ID.
        
        Args:
            paper_id: The paper identifier
            
        Returns:
            PaperData object or None if not found
        """
        pass
    
    def validate_paper(self, paper: PaperData) -> bool:
        """
        Validate that a paper has required fields.
        
        Args:
            paper: PaperData object to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["title", "abstract", "authors"]
        is_valid = all(getattr(paper, field, None) for field in required_fields)
        
        if not is_valid:
            self.logger.debug(f"Invalid paper: missing required fields - {paper.title[:50]}")
        
        return is_valid
