"""
zenodo_client.py - Zenodo API Client

Client for fetching papers from Zenodo (https://zenodo.org).
Zenodo is an open-access repository maintained by CERN with no rate limits.

API Documentation: https://developers.zenodo.org/
"""

import time
from typing import List, Optional

import requests

from ingestion.clients.base import BaseAPIClient, PaperData


class ZenodoClient(BaseAPIClient):
    """
    Fetch papers from Zenodo API.
    
    Zenodo provides unlimited access, no rate limiting.
    Great for open access research papers with full metadata.
    """
    
    BASE_URL = "https://zenodo.org/api/records"
    
    # Rate limiting: Zenodo has NO strict rate limits (generous!)
    REQUEST_DELAY = 0.5  # seconds between requests (very conservative, optional)
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds between retries
    
    def __init__(self, timeout: int = 30):
        """
        Initialize Zenodo client.
        
        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self._last_request_time: float = 0
    
    @property
    def source_name(self) -> str:
        return "Zenodo"
    
    def search(self, query: str, max_results: int = 100) -> List[PaperData]:
        """
        Search Zenodo for papers.
        
        Args:
            query: Search query (e.g., "software testing")
            max_results: Number of results to fetch (max 10000 per request)
            
        Returns:
            List of PaperData objects
        """
        self.logger.info(f"Searching Zenodo for: '{query}'")
        
        # Zenodo search parameters
        # Filter for publications (papers, articles, etc.)
        params = {
            "q": f'"{query}" AND type:publication',
            "size": min(max_results, 100),  # Max 100 per page
            "sort": "-publication_date",  # Sort by newest first
            "all_versions": False,  # Only latest versions
        }
        
        papers: List[PaperData] = []
        page = 0
        
        try:
            while len(papers) < max_results:
                params["page"] = page + 1
                
                self._wait_if_needed()
                response = None
                
                # Retry logic for transient failures
                for attempt in range(self.MAX_RETRIES):
                    self._last_request_time = time.time()
                    
                    try:
                        response = requests.get(
                            self.BASE_URL,
                            params=params,
                            timeout=self.timeout,
                        )
                        response.raise_for_status()
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt < self.MAX_RETRIES - 1:
                            wait = self.RETRY_DELAY * (attempt + 1)
                            self.logger.warning(
                                f"Zenodo request failed (attempt {attempt + 1}/{self.MAX_RETRIES}), "
                                f"retrying in {wait}s..."
                            )
                            time.sleep(wait)
                        else:
                            raise
                
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                
                # No more results
                if not hits:
                    break
                
                # Parse papers from this page
                for hit in hits:
                    paper = self._parse_hit(hit)
                    if paper and self.validate_paper(paper):
                        papers.append(paper)
                        if len(papers) >= max_results:
                            break
                
                page += 1
            
            valid_papers = papers[:max_results]
            self.logger.info(f"Found {len(valid_papers)} valid papers from Zenodo")
            return valid_papers
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching Zenodo: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error parsing Zenodo response: {e}")
            return []
    
    def _wait_if_needed(self) -> None:
        """Optional rate limiting (Zenodo doesn't require it, but be respectful)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
    
    def _parse_hit(self, hit: dict) -> Optional[PaperData]:
        """Parse a single Zenodo hit into PaperData."""
        try:
            metadata = hit.get("metadata", {})
            
            # Extract title
            title = metadata.get("title", "")
            if not title:
                return None
            
            # Extract abstract (may or may not be present)
            abstract = metadata.get("description", "")
            
            # Extract authors
            creators = metadata.get("creators", [])
            authors = []
            for creator in creators:
                if isinstance(creator, dict):
                    name = creator.get("name", "")
                    if name:
                        authors.append(name)
                elif isinstance(creator, str):
                    authors.append(creator)
            
            # Extract publication year
            year = None
            publication_date = metadata.get("publication_date")
            if publication_date:
                try:
                    year = int(publication_date.split("-")[0])
                except (ValueError, IndexError):
                    year = None
            
            # Extract DOI
            doi = metadata.get("doi")
            
            # Extract URL
            url = hit.get("links", {}).get("self_html", "")
            if not url:
                # Fallback to record URL
                record_id = hit.get("id")
                if record_id:
                    url = f"https://zenodo.org/record/{record_id}"
            
            # Extract venue/keywords
            keywords = metadata.get("keywords", [])
            venue = keywords[0] if keywords else None
            
            return PaperData(
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                doi=doi,
                url=url,
                venue=venue,
                source=self.source_name,
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing Zenodo hit: {e}")
            return None
    
    def get_paper(self, record_id: str) -> Optional[PaperData]:
        """
        Get a specific paper by Zenodo record ID.
        
        Args:
            record_id: The Zenodo record identifier
            
        Returns:
            PaperData object or None if not found
        """
        url = f"{self.BASE_URL}/{record_id}"
        
        try:
            self._wait_if_needed()
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            hit = response.json()
            return self._parse_hit(hit)
            
        except Exception as e:
            self.logger.error(f"Error fetching paper {record_id}: {e}")
            return None