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
    
    API_ENDPOINTS = [
        ("https://doaj.org/api/search/articles", True),
        ("https://doaj.org/api/search/articles", False),
        ("https://doaj.org/api/v1/search/articles", False),
    ]
    
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
        self._endpoint_index: int = 0
    
    @property
    def source_name(self) -> str:
        return "DOAJ"
    
    def search(self, query: str, max_results: int = 100) -> List[PaperData]:
        """
        Search DOAJ for papers with Computer Science filtering.
        
        Args:
            query: Search query (e.g., "software testing")
            max_results: Number of results to fetch
            
        Returns:
            List of PaperData objects
        """
        self.logger.info(f"Searching DOAJ for: '{query}'")
        
        papers: List[PaperData] = []
        page = 1
        page_size = 20  # Reduced from 100 for reliability
        
        try:
            while len(papers) < max_results:
                # Build DOAJ query with Software Engineering specific filtering
                # Query in 'q' parameter, not in URL path
                # Focus on Software Engineering, Testing, Development, Quality Assurance
                doaj_query = (
                    f'(title:("{query}") OR abstract:("{query}") OR keywords:("{query}")) '
                    f'AND (subject:"Software Engineering" OR subject:"Software Testing" OR '
                    f'subject:"Software Development" OR subject:"Software Quality" OR '
                    f'keywords:("software engineering" OR "software testing" OR "test case" OR '
                    f'"quality assurance" OR "software development" OR "bug detection" OR '
                    f'"code review" OR "requirements engineering" OR "software maintenance"))'
                )
                
                params = {
                    "pageSize": page_size,
                    "page": page,
                }
                
                self._wait_if_needed()
                response = None
                
                # Retry logic for transient failures
                for attempt in range(self.MAX_RETRIES):
                    self._last_request_time = time.time()
                    
                    try:
                        base_url, use_path_query = self.API_ENDPOINTS[self._endpoint_index]
                        request_params = dict(params)
                        request_url = base_url

                        if use_path_query:
                            request_url = f"{base_url}/{query}"
                        else:
                            request_params["q"] = doaj_query

                        response = requests.get(
                            request_url,
                            params=request_params,
                            timeout=self.timeout,
                        )

                        if response.status_code == 404:
                            if self._try_next_endpoint():
                                next_url, next_is_path = self.API_ENDPOINTS[self._endpoint_index]
                                mode = "path" if next_is_path else "q-parameter"
                                self.logger.warning(
                                    f"DOAJ endpoint returned 404, switching to {next_url} ({mode})"
                                )
                                continue
                            self.logger.error("All DOAJ endpoint variants returned 404")
                            return papers
                        
                        # Check status immediately before using response
                        if response.status_code == 400:
                            self.logger.error(f"Bad request: {response.text}")
                            return papers  # Return what we have so far
                        
                        if response.status_code == 429:
                            # Handle rate limiting
                            wait = int(response.headers.get("Retry-After", 60))
                            self.logger.warning(f"Rate limited by DOAJ, waiting {wait}s...")
                            time.sleep(wait)
                            continue
                        
                        if response.status_code >= 500:
                            # Handle server errors with retry
                            if attempt < self.MAX_RETRIES - 1:
                                wait = self.RETRY_DELAY * (attempt + 1)
                                self.logger.warning(
                                    f"DOAJ server error ({response.status_code}), "
                                    f"retrying in {wait}s..."
                                )
                                time.sleep(wait)
                                continue
                        
                        response.raise_for_status()
                        break  # Success!
                        
                    except requests.exceptions.Timeout:
                        if attempt < self.MAX_RETRIES - 1:
                            wait = self.RETRY_DELAY * (attempt + 1)
                            self.logger.warning(
                                f"DOAJ request timeout (attempt {attempt + 1}/{self.MAX_RETRIES}), "
                                f"retrying in {wait}s..."
                            )
                            time.sleep(wait)
                        else:
                            self.logger.error("DOAJ request timeout - max retries exceeded")
                            return papers  # Return what we have so far
                            
                    except requests.exceptions.ConnectionError:
                        if attempt < self.MAX_RETRIES - 1:
                            wait = self.RETRY_DELAY * (attempt + 1)
                            self.logger.warning(
                                f"Connection error (attempt {attempt + 1}/{self.MAX_RETRIES}), "
                                f"retrying in {wait}s..."
                            )
                            time.sleep(wait)
                        else:
                            self.logger.error("Connection error - max retries exceeded")
                            return papers  # Return what we have so far
                            
                    except requests.exceptions.RequestException as e:
                        if attempt < self.MAX_RETRIES - 1:
                            wait = self.RETRY_DELAY * (attempt + 1)
                            self.logger.warning(
                                f"DOAJ request failed (attempt {attempt + 1}/{self.MAX_RETRIES}), "
                                f"retrying in {wait}s... Error: {e}"
                            )
                            time.sleep(wait)
                        else:
                            self.logger.error(f"DOAJ request failed after {self.MAX_RETRIES} attempts")
                            return papers  # Return what we have so far
                
                if response is None:
                    break
                
                data = response.json()
                results = data.get("results", [])
                
                # No more results
                if not results:
                    break
                
                # Parse papers from this page
                for result in results:
                    paper = self._parse_result(result)
                    if (
                        paper
                        and self.validate_paper(paper)
                        and self._is_software_engineering_relevant(paper, query)
                    ):
                        papers.append(paper)
                        if len(papers) >= max_results:
                            break
                
                # Stop if we got fewer results than requested (last page)
                if len(results) < page_size:
                    break
                
                page += 1
            
            valid_papers = papers[:max_results]
            self.logger.info(f"Found {len(valid_papers)} valid papers from DOAJ")
            return valid_papers
            
        except Exception as e:
            self.logger.error(f"Unexpected error searching DOAJ: {e}")
            return papers  # Return what we have so far

    def _try_next_endpoint(self) -> bool:
        """Try the next known DOAJ endpoint variant."""
        if self._endpoint_index < len(self.API_ENDPOINTS) - 1:
            self._endpoint_index += 1
            return True
        return False

    def _is_software_engineering_relevant(self, paper: PaperData, query: str) -> bool:
        """Enforce software engineering relevance even when endpoint filtering is limited."""
        se_terms = [
            "software engineering",
            "software testing",
            "unit testing",
            "integration testing",
            "test case",
            "quality assurance",
            "software quality",
            "software maintenance",
            "requirements engineering",
            "code review",
            "bug",
            "debugging",
        ]

        query_terms = [t.strip().lower() for t in query.split() if t.strip()]
        haystack = " ".join(
            [
                paper.title or "",
                paper.abstract or "",
                paper.venue or "",
            ]
        ).lower()

        has_se_signal = any(term in haystack for term in se_terms)
        has_query_signal = any(term in haystack for term in query_terms)
        return has_se_signal and has_query_signal
    
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