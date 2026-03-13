"""
arxiv_client.py - arXiv API Client

Client for fetching papers from arXiv API.
arXiv is ideal for computer science preprints and recent research.

API Documentation: https://arxiv.org/help/api/user-manual
"""

import time
import xml.etree.ElementTree as ET
from typing import List, Optional

import requests

from ingestion.clients.base import BaseAPIClient, PaperData


class ArxivClient(BaseAPIClient):
    """
    Fetch papers from arXiv API.
    
    Respects rate limiting: max 1 request per 3 seconds.
    Targets computer science categories relevant to SE research.
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    # arXiv categories for software engineering research
    CS_CATEGORIES = [
        "cs.SE",  # Software Engineering
        "cs.PL",  # Programming Languages
        "cs.CY",  # Computers and Society
        "cs.LG",  # Machine Learning (for ML4SE papers)
    ]
    
    def __init__(self, timeout: int = 30, delay: float = 5.0):
        """
        Initialize arXiv client.
        
        Args:
            timeout: Request timeout in seconds
            delay: Delay between requests (arXiv requires 3+ seconds, using 5s for safety)
        """
        super().__init__(timeout)
        self.delay = delay
        self._last_request_time: float = 0
    
    @property
    def source_name(self) -> str:
        return "arXiv"
    
    def _wait_if_needed(self) -> None:
        """Respect arXiv's rate limit: max 1 request per 3 seconds."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()
    
    def search(self, query: str, max_results: int = 100) -> List[PaperData]:
        """
        Search arXiv for papers.
        
        Args:
            query: Search query (e.g., "software testing")
            max_results: Number of results to fetch (max 10000)
            
        Returns:
            List of PaperData objects
        """
        self.logger.info(f"Searching arXiv for: '{query}'")
        
        # Build arXiv search query with CS category filter
        category_filter = " OR ".join(f"cat:{cat}" for cat in self.CS_CATEGORIES)
        arxiv_query = f'({category_filter}) AND all:"{query}"'
        
        params = {
            "search_query": arxiv_query,
            "start": 0,
            "max_results": min(max_results, 10000),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        
        try:
            self._wait_if_needed()
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            papers = self._parse_response(response.content)
            valid_papers = [p for p in papers if self.validate_paper(p)]
            
            self.logger.info(f"Found {len(valid_papers)} valid papers from arXiv")
            return valid_papers
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching from arXiv: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error parsing arXiv response: {e}")
            return []
    
    def _parse_response(self, content: bytes) -> List[PaperData]:
        """Parse arXiv XML response into PaperData objects."""
        papers = []
        root = ET.fromstring(content)
        
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        for entry in root.findall("atom:entry", ns):
            paper = self._parse_entry(entry, ns)
            if paper:
                papers.append(paper)
        
        return papers
    
    def _parse_entry(self, entry: ET.Element, ns: dict) -> Optional[PaperData]:
        """Parse a single arXiv XML entry into PaperData."""
        try:
            # Extract title (remove newlines and extra whitespace)
            title_elem = entry.find("atom:title", ns)
            title = " ".join(title_elem.text.split()) if title_elem is not None else ""
            
            # Extract abstract
            summary_elem = entry.find("atom:summary", ns)
            abstract = " ".join(summary_elem.text.split()) if summary_elem is not None else ""
            
            # Extract authors
            authors = [
                author.find("atom:name", ns).text
                for author in entry.findall("atom:author", ns)
                if author.find("atom:name", ns) is not None
            ]
            
            # Extract year from published date (format: YYYY-MM-DDTHH:MM:SSZ)
            published_elem = entry.find("atom:published", ns)
            year = None
            if published_elem is not None and published_elem.text:
                year = int(published_elem.text.split("-")[0])
            
            # Extract arXiv ID from entry ID URL
            id_elem = entry.find("atom:id", ns)
            arxiv_id = ""
            if id_elem is not None and id_elem.text:
                arxiv_id = id_elem.text.split("/abs/")[-1]
            
            return PaperData(
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                doi=arxiv_id,
                url=f"https://arxiv.org/abs/{arxiv_id}",
                source=self.source_name,
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing arXiv entry: {e}")
            return None
    
    def get_paper(self, arxiv_id: str) -> Optional[PaperData]:
        """
        Get a specific paper by arXiv ID.
        
        Args:
            arxiv_id: The arXiv paper identifier
            
        Returns:
            PaperData object or None if not found
        """
        params = {"id_list": arxiv_id, "max_results": 1}
        
        try:
            self._wait_if_needed()
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            papers = self._parse_response(response.content)
            return papers[0] if papers else None
            
        except Exception as e:
            self.logger.error(f"Error fetching paper {arxiv_id}: {e}")
            return None
