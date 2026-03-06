"""  
Data Ingestion Package

Components for fetching research papers from external APIs
and populating the database with processed paper data.
"""

from ingestion.clients import ArxivClient, DBLPClient, PaperData, SemanticScholarClient
from ingestion.processors import PaperCategorizer, PaperProcessor

__all__ = [
    "ArxivClient",
    "SemanticScholarClient",
    "DBLPClient",
    "PaperData",
    "PaperProcessor",
    "PaperCategorizer",
]
