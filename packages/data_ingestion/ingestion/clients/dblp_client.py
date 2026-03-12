"""
dblp_client.py - DBLP API Client

Client for fetching papers from DBLP (Computer Science Bibliography).
DBLP focuses on peer-reviewed CS publications with high-quality metadata.

API Documentation: https://dblp.org/faq/How+to+use+the+dblp+search+API.html
"""

import time
from typing import List, Optional

import requests

from ingestion.clients.base import BaseAPIClient, PaperData


class DBLPClient(BaseAPIClient):
    """
    Fetch papers from DBLP API.
    
    DBLP provides indexed, peer-reviewed computer science papers.
    Excellent for established venues and conferences.
    """
    
    BASE_URL = "https://dblp.org/search/publ/api"
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds between retries
    REQUEST_DELAY = 1.0  # seconds between requests
    
    def __init__(self, timeout: int = 30):
        """
        Initialize DBLP client.
        
        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self._last_request_time: float = 0
    
    @property
    def source_name(self) -> str:
        return "DBLP"
    
    def search(self, query: str, max_results: int = 100) -> List[PaperData]:
        """
        Search DBLP for papers.
        
        Args:
            query: Search query
            max_results: Number of results (max 1000)
            
        Returns:
            List of PaperData objects
        """
        self.logger.info(f"Searching DBLP for: '{query}'")
        
        params = {
            "q": query,
            "h": min(max_results, 1000),
            "format": "json",
        }
        
        try:
            # Rate limiting
            elapsed = time.time() - self._last_request_time
            if elapsed < self.REQUEST_DELAY:
                time.sleep(self.REQUEST_DELAY - elapsed)
            
            response = None
            for attempt in range(self.MAX_RETRIES):
                self._last_request_time = time.time()
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.timeout,
                )
                
                if response.status_code in (500, 502, 503):
                    if attempt < self.MAX_RETRIES - 1:
                        wait = self.RETRY_DELAY * (attempt + 1)
                        self.logger.warning(
                            f"DBLP returned {response.status_code}, retrying in {wait}s "
                            f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        time.sleep(wait)
                        continue
                
                break
            
            response.raise_for_status()
            
            data = response.json()
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            
            papers = [self._parse_hit(hit) for hit in hits]
            valid_papers = [p for p in papers if p and self.validate_paper(p)]
            
            self.logger.info(f"Found {len(valid_papers)} valid papers from DBLP")
            return valid_papers
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching DBLP: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []
    
    def _parse_hit(self, hit: dict) -> Optional[PaperData]:
        """Parse DBLP API hit into PaperData."""
        try:
            info = hit.get("info", {})
            
            # Extract authors (can be list or single dict)
            authors_raw = info.get("authors", {}).get("author", [])
            if isinstance(authors_raw, dict):
                authors = [authors_raw.get("text", "")]
            elif isinstance(authors_raw, list):
                authors = [
                    a.get("text", "") if isinstance(a, dict) else str(a)
                    for a in authors_raw
                ]
            else:
                authors = []
            
            # Extract year with validation
            year_str = info.get("year")
            year = int(year_str) if year_str and year_str.isdigit() else None
            
            return PaperData(
                title=info.get("title", ""),
                abstract="",  # DBLP doesn't provide abstracts
                authors=[a for a in authors if a],
                year=year,
                doi=info.get("doi"),
                url=info.get("url"),
                venue=info.get("venue"),
                source=self.source_name,
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing DBLP hit: {e}")
            return None
    
    def get_paper(self, dblp_key: str) -> Optional[PaperData]:
        """
        Get paper by DBLP key.
        
        Note: DBLP API doesn't support direct key-based lookup.
        
        Args:
            dblp_key: The DBLP paper key
            
        Returns:
            None (not supported)
        """
        self.logger.warning("DBLP API doesn't support direct key-based lookup")
        return None
