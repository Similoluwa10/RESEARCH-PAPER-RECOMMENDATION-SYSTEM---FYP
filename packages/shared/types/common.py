"""
Common Types

Shared type definitions.
"""

from typing import Dict, List, Optional, TypedDict
from uuid import UUID


class PaperDict(TypedDict):
    """Paper dictionary type."""
    id: str
    title: str
    abstract: str
    authors: List[str]
    year: int
    venue: Optional[str]
    keywords: List[str]


class RecommendationDict(TypedDict):
    """Recommendation dictionary type."""
    paper_id: str
    score: float
    method: str


class ExplanationDict(TypedDict):
    """Explanation dictionary type."""
    summary: str
    key_terms: List[str]
    similarity_breakdown: Dict[str, float]


class EvaluationResultDict(TypedDict):
    """Evaluation result dictionary type."""
    method: str
    metrics: Dict[str, float]
    params: Dict[str, any]
