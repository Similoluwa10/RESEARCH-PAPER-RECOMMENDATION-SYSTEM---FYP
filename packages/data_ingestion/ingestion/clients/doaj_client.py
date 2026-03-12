"""
doaj_client.py - DOAJ API Client

Client for fetching papers from DOAJ (Directory of Open Access Journals).
DOAJ is a curated list of high-quality open access journals with no rate limits.

API Documentation: https://doaj.org/api/v1/docs
"""

import time
from typing import List, Optional

import requests

from ingestion.clients.base import BaseAPIClient, PaperData


class DOAJClient(BaseAPIClient):
    """
    Fetch papers from DOAJ API.
    
    DOAJ provides access to millions of articles from quality-controlled
    open access journals. No rate limiting, unlimited requests.
    """
    
    BASE_URL = "https://doaj.org/api/search/articles"
    
    # Rate limiting: DOAJ has NO strict rate limits (very generous!)
    REQUEST_DELAY = 0.3  # seconds between requests (optional, very fast)
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds between retries
    
    def __init__(self, timeout: int = 30):
        """
        Initialize DOAJ client.
        
        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self._last_request_time: float = 0
    
    @property
    def source_name(self) -> str:
        return "DOAJ"
    
    def search(self, query: str, max_results: int = 100) -> List[PaperData]:
        """
        Search DOAJ for papers.
        
        Args:
            query: Search query (e.g., "software testing")
            max_results: Number of results to fetch
            
        Returns:
            List of PaperData objects
        """
        self.logger.info(f"Searching DOAJ for: '{query}'")
        
        papers: List[PaperData] = []
        page = 0
        page_size = 100  # DOAJ returns max 100 per page
        
        try:
            while len(papers) < max_results:
                # DOAJ uses offset-based pagination
                offset = page * page_size
                
                # Note: DOAJ API expects search query in the URL path
                params = {
                    "page": page + 1,  # DOAJ uses 1-indexed pages
                    "pageSize": page_size,
                }
                
                self._wait_if_needed()
                response = None
                
                # Retry logic for transient failures
                for attempt in range(self.MAX_RETRIES):
                    self._last_request_time = time.time()
                    
                    try:
                        # Construct URL with search query in path
                        url = f"{self.BASE_URL}/{query}"
                        response = requests.get(
                            url,
                            params=params,
                            timeout=self.timeout,
                        )
                        response.raise_for_status()
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt < self.MAX_RETRIES - 1:
                            wait = self.RETRY_DELAY * (attempt + 1)
                            self.logger.warning(
                                f"DOAJ request failed (attempt {attempt + 1}/{self.MAX_RETRIES}), "
                                f"retrying in {wait}s..."
                            )
                            time.sleep(wait)
                        else:
                            raise
                
                data = response.json()
                results = data.get("results", [])
                
                # No more results
                if not results:
                    break
                
                # Parse papers from this page
                for result in results:
                    paper = self._parse_result(result)
                    if paper and self.validate_paper(paper):
                        papers.append(paper)
                        if len(papers) >= max_results:
                            break
                
                page += 1
            
            valid_papers = papers[:max_results]
            self.logger.info(f"Found {len(valid_papers)} valid papers from DOAJ")
            return valid_papers
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching DOAJ: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error parsing DOAJ response: {e}")
            return []
    
    def _wait_if_needed(self) -> None:
        """Optional rate limiting (DOAJ doesn't require it, but be respectful)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
    
    def _parse_result(self, result: dict) -> Optional[PaperData]:
        """Parse a single DOAJ article result into PaperData."""
        try:
            # Extract bibjson (main metadata)
            bibjson = result.get("bibjson", {})
            
            # Extract title
            title = bibjson.get("title", "")
            if not title:
                return None
            
            # Extract abstract
            abstract = bibjson.get("abstract", "")
            
            # Extract authors
            author_list = bibjson.get("author", [])
            authors = []
            for author in author_list:
                if isinstance(author, dict):
                    name = author.get("name", "")
                    if name:
                        authors.append(name)
                elif isinstance(author, str):
                    authors.append(author)
            
            # Extract publication year
            year = None
            published = bibjson.get("year")
            if published:
                try:
                    year = int(str(published).split("-")[0])
                except (ValueError, IndexError, AttributeError):
                    year = None
            
            # Extract DOI
            identifiers = bibjson.get("identifier", [])
            doi = None
            for identifier in identifiers:
                if isinstance(identifier, dict):
                    if identifier.get("type") == "doi":
                        doi = identifier.get("id")
                        break
            
            # Extract URL
            links = bibjson.get("link", [])
            url = None
            for link in links:
                if isinstance(link, dict):
                    if link.get("type") == "fulltext":
                        url = link.get("url")
                        break
            
            # Extract venue (journal title)
            venue = bibjson.get("journal", {}).get("title") if isinstance(bibjson.get("journal"), dict) else None
            
            # Extract keywords
            keywords = bibjson.get("keywords", [])
            
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
            self.logger.debug(f"Error parsing DOAJ result: {e}")
            return None
    
    def get_paper(self, article_id: str) -> Optional[PaperData]:
        """
        Get a specific paper by DOAJ article ID.
        
        Note: DOAJ API doesn't support direct ID lookup.
        Use search() instead.
        
        Args:
            article_id: The DOAJ article identifier
            
        Returns:
            None (not supported by API)
        """
        self.logger.warning("DOAJ API doesn't support direct article ID lookup")
        return None