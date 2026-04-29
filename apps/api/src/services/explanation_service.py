"""
explanation_service.py - Explanation Service (XAI)

Generates human-readable explanations for recommendations using LangChain.
Core component for the "Explainable" aspect of the system.
"""

import logging
from typing import Any, List

from src.schemas.recommendation import RecommendationExplanation
from src.services.langchain_explainer import LangChainExplainer

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Service for generating recommendation explanations.
    
    Uses LangChain for LLM-based explanations with fallback to heuristics.
    Provides explainability features to help users understand
    why specific papers were recommended.
    """
    
    def __init__(self):
        """Initialize LangChain explainer with fallback support."""
        self.langchain_explainer = LangChainExplainer()
        self.use_langchain = self.langchain_explainer.is_available()
        
        if self.use_langchain:
            logger.info("Using LangChain for explanations")
        else:
            logger.warning("LangChain unavailable, using fallback explanations")
    
    def generate_explanation(
        self,
        query_text: str,
        paper: Any,
        similarity_score: float,
    ) -> RecommendationExplanation:
        """
        Generate a full explanation for a recommendation.
        
        Uses LangChain if available, falls back to heuristics otherwise.
        
        Args:
            query_text: The user's search query or paper text
            paper: The recommended paper
            similarity_score: Overall similarity score (0-1)
            
        Returns:
            Explanation dictionary with summary, reasoning, and metadata
        """
        key_terms = self.extract_key_terms(query_text, paper)
        
        if self.use_langchain:
            result = self.langchain_explainer.generate_explanation(
                query=query_text,
                paper=paper,
                similarity_score=similarity_score,
                key_terms=key_terms,
            )
        else:
            result = self._generate_heuristic_explanation(
                query_text, paper, similarity_score, key_terms
            )
        
        return RecommendationExplanation.from_model(result)
    
    def extract_key_terms(
        self,
        query: str,
        paper: Any,
    ) -> List[str]:
        """
        Extract key terms that contributed to the match.
        
        Identifies shared concepts between query and paper using simple
        keyword overlap analysis.
        
        Args:
            query: Search query text
            paper: The matched paper
            
        Returns:
            List of important matching terms (up to 5)
        """
        query_words = set(
            word.lower() for word in query.split() 
            if len(word) > 4  # Only significant words
        )
        
        paper_text = f"{paper.title} {paper.abstract}".lower()
        paper_words = set(
            word.lower() for word in paper_text.split()
            if len(word) > 4
        )
        
        # Find overlapping important terms
        overlap = query_words & paper_words
        
        # Sort and limit to top 5
        return sorted(list(overlap))[:5]
    
    def _generate_heuristic_explanation(
        self,
        query: str,
        paper: Any,
        similarity_score: float,
        key_terms: List[str],
    ) -> dict:
        """Generate explanation using heuristic rules when LLM unavailable."""
        # Determine strength of match
        if similarity_score >= 0.8:
            strength = "highly"
        elif similarity_score >= 0.6:
            strength = "moderately"
        else:
            strength = "somewhat"
        
        # Build explanation
        if key_terms:
            terms_str = ", ".join(key_terms[:3])
            summary = f"This paper is {strength} relevant due to shared concepts: {terms_str}."
        else:
            summary = f"This paper is {strength} relevant based on semantic similarity ({similarity_score:.0%})."
        
        # Assess confidence
        if similarity_score >= 0.7:
            confidence = "high"
        elif similarity_score >= 0.4:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "summary": summary,
            "reasoning_steps": f"Heuristic analysis: Similarity Score {similarity_score:.2%}",
            "key_terms": key_terms,
            "confidence": confidence,
        }
    
    def compute_similarity_breakdown(
        self,
        query: str,
        paper: Any,
    ) -> dict:
        """
        Break down the similarity score by component.
        
        Shows contribution of semantic vs keyword matching.
        
        Args:
            query: Search query text
            paper: The matched paper
            
        Returns:
            Dictionary with component scores
        """
        # TODO: Implement detailed similarity analysis
        return {
            "semantic_similarity": 0.0,
            "keyword_overlap": 0.0,
            "title_match": 0.0,
            "abstract_match": 0.0,
            "overall": 0.0,
        }
