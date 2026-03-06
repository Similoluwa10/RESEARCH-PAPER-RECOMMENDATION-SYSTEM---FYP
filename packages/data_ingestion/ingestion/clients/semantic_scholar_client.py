"""
semantic_scholar_client.py - Semantic Scholar API Client

Client for fetching papers from Semantic Scholar API.
Provides enriched metadata including citations and references.

API Documentation: https://www.semanticscholar.org/product/api
"""

from typing import List, Optional

import requests

from ingestion.clients.base import BaseAPIClient, PaperData


class SemanticScholarClient(BaseAPIClient):
    """
    Fetch papers from Semantic Scholar API.
    
    Semantic Scholar provides high-quality metadata and citation data.
    Free tier has rate limits; API keys available for higher limits.
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    # Fields to retrieve from API
    PAPER_FIELDS = "paperId,title,abstract,authors,year,doi,url,venue"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize Semantic Scholar client.
        
        Args:
            api_key: Optional API key for higher rate limits
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self.api_key = api_key
        self._headers = {"x-api-key": api_key} if api_key else {}
    
    @property
    def source_name(self) -> str:
        return "Semantic Scholar"
    
    def search(self, query: str, max_results: int = 100) -> List[PaperData]:
        """
        Search Semantic Scholar for papers.
        
        Args:
            query: Search query
            max_results: Number of results (max 100 per request)
            
        Returns:
            List of PaperData objects
        """
        self.logger.info(f"Searching Semantic Scholar for: '{query}'")
        
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": self.PAPER_FIELDS,
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            papers = [
                self._parse_paper(p)
                for p in data.get("data", [])
            ]
            valid_papers = [p for p in papers if p and self.validate_paper(p)]
            
            self.logger.info(f"Found {len(valid_papers)} valid papers from Semantic Scholar")
            return valid_papers
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching Semantic Scholar: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []
    
    def _parse_paper(self, paper_data: dict) -> Optional[PaperData]:
        """Parse Semantic Scholar API response into PaperData."""
        try:
            # Extract authors (API returns list of author dicts)
            authors = [
                author.get("name", "")
                for author in paper_data.get("authors", [])
                if author.get("name")
            ]
            
            return PaperData(
                title=paper_data.get("title", ""),
                abstract=paper_data.get("abstract") or "",
                authors=authors,
                year=paper_data.get("year"),
                doi=paper_data.get("doi"),
                url=paper_data.get("url"),
                venue=paper_data.get("venue"),
                source=self.source_name,
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing Semantic Scholar paper: {e}")
            return None
    
    def get_paper(self, paper_id: str) -> Optional[PaperData]:
        """
        Get paper by Semantic Scholar ID or DOI.
        
        Args:
            paper_id: Semantic Scholar paper ID or DOI
            
        Returns:
            PaperData object or None if not found
        """
        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {"fields": self.PAPER_FIELDS}
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            return self._parse_paper(response.json())
            
        except Exception as e:
            self.logger.error(f"Error fetching paper {paper_id}: {e}")
            return None
