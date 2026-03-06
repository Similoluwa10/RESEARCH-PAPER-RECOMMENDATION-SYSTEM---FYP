"""
API Clients Package

Clients for fetching papers from external academic APIs.
"""

from ingestion.clients.base import BaseAPIClient, PaperData
from ingestion.clients.arxiv_client import ArxivClient
from ingestion.clients.dblp_client import DBLPClient
from ingestion.clients.semantic_scholar_client import SemanticScholarClient

__all__ = [
    "BaseAPIClient",
    "PaperData",
    "ArxivClient",
    "SemanticScholarClient",
    "DBLPClient",
]
