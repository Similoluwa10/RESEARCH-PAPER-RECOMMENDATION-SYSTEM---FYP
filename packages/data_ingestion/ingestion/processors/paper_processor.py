"""
paper_processor.py - Paper Processor

Processes and cleans paper data from API clients.
Handles deduplication, text cleaning, and validation.
"""

import html
import logging
import re
from difflib import SequenceMatcher
from typing import List, Optional

from ingestion.clients.base import PaperData


class LoggerMixin:
    """Mixin class to add logging capability."""
    
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)


class PaperProcessor(LoggerMixin):
    """
    Process, clean, and deduplicate paper data.
    
    Applies text normalization, removes duplicates based on
    title similarity, and validates required fields.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize processor.
        
        Args:
            similarity_threshold: Threshold for considering titles as duplicates (0-1)
        """
        self.similarity_threshold = similarity_threshold
    
    def process_papers(self, papers: List[PaperData]) -> List[PaperData]:
        """
        Process a list of papers.
        
        Applies cleaning, deduplication, and validation in sequence.
        
        Args:
            papers: List of PaperData objects
            
        Returns:
            List of cleaned, unique, validated papers
        """
        self.logger.info(f"Processing {len(papers)} papers...")
        
        # Step 1: Clean each paper
        cleaned = [self._clean_paper(p) for p in papers]
        cleaned = [p for p in cleaned if p is not None]
        self.logger.info(f"After cleaning: {len(cleaned)} papers")
        
        # Step 2: Remove duplicates
        unique = self._deduplicate(cleaned)
        self.logger.info(f"After deduplication: {len(unique)} papers")
        
        return unique
    
    def _clean_paper(self, paper: PaperData) -> Optional[PaperData]:
        """
        Clean paper data.
        
        Normalizes text, removes HTML, and validates minimum content.
        """
        try:
            # Clean title
            paper.title = self._clean_text(paper.title)
            if not paper.title or len(paper.title) < 10:
                return None
            
            # Clean abstract
            paper.abstract = self._clean_text(paper.abstract)
            if not paper.abstract or len(paper.abstract) < 50:
                return None
            
            # Clean authors
            paper.authors = [
                self._clean_text(a)
                for a in paper.authors
                if self._clean_text(a)
            ]
            if not paper.authors:
                return None
            
            # Validate year range
            if paper.year and (paper.year < 1990 or paper.year > 2100):
                paper.year = None
            
            return paper
            
        except Exception as e:
            self.logger.debug(f"Error cleaning paper: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text content.
        
        Removes HTML tags, decodes entities, and normalizes whitespace.
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        
        return text.strip()
    
    def _deduplicate(self, papers: List[PaperData]) -> List[PaperData]:
        """
        Remove duplicate papers based on title similarity.
        
        Uses sequence matching to identify near-duplicate titles.
        """
        unique: List[PaperData] = []
        seen_titles: List[str] = []
        duplicates = 0
        
        for paper in papers:
            normalized = self._normalize_title(paper.title)
            
            is_duplicate = any(
                self._string_similarity(normalized, seen) > self.similarity_threshold
                for seen in seen_titles
            )
            
            if is_duplicate:
                duplicates += 1
                self.logger.debug(f"Duplicate found: {paper.title[:50]}...")
            else:
                unique.append(paper)
                seen_titles.append(normalized)
        
        self.logger.info(f"Removed {duplicates} duplicates")
        return unique
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        return re.sub(r"[^\w\s]", "", title).lower()
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings (0-1)."""
        return SequenceMatcher(None, s1, s2).ratio()
