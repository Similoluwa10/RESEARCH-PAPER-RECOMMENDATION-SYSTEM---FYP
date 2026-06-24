"""
explanation_service.py - Explanation Service (XAI)

Generates human-readable explanations for recommendations using LangChain.
Core component for the "Explainable" aspect of the system.

Supports concurrent async explanation generation via asyncio.Semaphore
for improved performance when processing multiple papers.
"""

import asyncio
import logging
from typing import Any, List, Optional

from src.schemas.recommendation import RecommendationExplanation
from src.services.langchain_explainer import LangChainExplainer

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Service for generating recommendation explanations.
    
    Uses LangChain for LLM-based explanations with fallback to heuristics.
    Provides explainability features to help users understand
    why specific papers were recommended.
    
    Supports concurrent async explanation generation via asyncio.Semaphore.
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize LangChain explainer with fallback support and concurrency control.
        
        Args:
            max_concurrent: Maximum number of concurrent LLM explanation requests.
                           Lower values reduce API rate limit issues, higher values
                           improve throughput. Default is 5.
        """
        self.langchain_explainer = LangChainExplainer()
        self.use_langchain = self.langchain_explainer.is_available()
        self._llm_failed = False  # Track if LLM has failed, disable subsequent attempts
        
        # Semaphore for controlling concurrent LLM calls
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        
        if self.use_langchain:
            logger.info(f"✓ Using LangChain for explanations (max {max_concurrent} concurrent)")
        else:
            logger.warning(
                "⚠ LangChain unavailable, using fallback explanations. "
                "Configure LANGCHAIN_PROVIDER and required API keys to enable LLM-based explanations."
            )
    
    async def generate_explanation(
        self,
        query_text: str,
        paper: Any,
        similarity_score: float,
    ) -> Optional[RecommendationExplanation]:
        """
        Generate a full explanation for a recommendation asynchronously.
        
        Uses LangChain if available, falls back to heuristics otherwise.
        If LLM fails on first attempt, all subsequent calls use heuristic.
        
        Respects concurrency limits via semaphore to avoid overwhelming LLM APIs.
        
        Args:
            query_text: The user's search query or paper text
            paper: The recommended paper
            similarity_score: Overall similarity score (0-1)
            
        Returns:
            Explanation object with summary, reasoning, and metadata
        """
        key_terms = self.extract_key_terms(query_text, paper)
        
        try:
            # If LLM already failed once, skip LLM attempts entirely
            if self.use_langchain and not self._llm_failed:
                # Acquire semaphore slot before making LLM call
                async with self.semaphore:
                    result = await self.langchain_explainer.generate_explanation(
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
        except Exception as e:
            logger.error(f"Error generating explanation (disabling LLM): {e}", exc_info=True)
            # Mark LLM as failed - all subsequent explanations will use heuristics
            self._llm_failed = True
            # Return heuristic explanation as fallback
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
        # Filter out common words and normalize
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
            'have', 'has', 'do', 'does', 'will', 'would', 'could', 'should',
            'that', 'this', 'these', 'those', 'which', 'who', 'what', 'when',
            'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'paper', 'research',
            'study', 'method', 'approach', 'using', 'based', 'etc'
        }
        
        query_words = set(
            word.lower().strip('.,;:!?()[]{}') 
            for word in query.split() 
            if len(word) > 3 and word.lower() not in common_words
        )
        
        paper_text = f"{paper.title or ''} {paper.abstract or ''}".lower()
        paper_words = set(
            word.lower().strip('.,;:!?()[]{}')
            for word in paper_text.split()
            if len(word) > 3 and word.lower() not in common_words
        )
        
        # Find overlapping important terms
        overlap = query_words & paper_words
        
        # Sort and limit to top 5
        key_terms = sorted(list(overlap))[:5]
        
        logger.debug(f"Extracted key terms: {key_terms}")
        return key_terms
    
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
            confidence = "high"
        elif similarity_score >= 0.6:
            strength = "moderately"
            confidence = "medium"
        elif similarity_score >= 0.4:
            strength = "somewhat"
            confidence = "medium"
        else:
            strength = "tangentially"
            confidence = "low"
        
        # Build explanation summary
        if key_terms:
            terms_str = ", ".join(key_terms[:3])
            summary = f"This paper is {strength} relevant due to shared concepts in {terms_str}."
        else:
            summary = f"This paper is {strength} relevant based on semantic similarity."
        
        # Add detail about the match quality
        if similarity_score >= 0.8:
            summary += " Strong thematic alignment with your query."
        elif similarity_score >= 0.5:
            summary += f" Similarity score: {similarity_score:.0%}"
        
        # Provide reasoning steps based on heuristics
        reasoning = []
        if key_terms:
            reasoning.append(f"• Key matching terms: {', '.join(key_terms[:3])}")
        reasoning.append(f"• Semantic similarity score: {similarity_score:.2%}")
        reasoning.append(f"• Confidence level: {confidence}")
        reasoning_text = "\n".join(reasoning)
        
        return {
            "summary": summary,
            "reasoning_steps": reasoning_text,
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
