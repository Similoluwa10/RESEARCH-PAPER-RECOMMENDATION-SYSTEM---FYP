"""
Explanation Generator

Generate human-readable explanations for recommendations.
"""

from typing import Dict, List

import numpy as np

from src.explainability.feature_importance import FeatureImportance


class ExplanationGenerator:
    """
    Generate natural language explanations for recommendations.
    
    Combines feature importance with template-based generation.
    """
    
    def __init__(self):
        self.feature_importance = FeatureImportance()
    
    def generate(
        self,
        query: str,
        recommended_title: str,
        similarity_score: float,
        key_terms: List[str],
        similarity_breakdown: Dict[str, float],
    ) -> Dict:
        """
        Generate a complete explanation.
        
        Args:
            query: Original query text
            recommended_title: Title of recommended paper
            similarity_score: Overall similarity score
            key_terms: Key matching terms
            similarity_breakdown: Breakdown of similarity components
            
        Returns:
            Explanation dictionary
        """
        summary = self._generate_summary(
            similarity_score,
            key_terms,
            similarity_breakdown,
        )
        
        return {
            "summary": summary,
            "key_terms": key_terms,
            "similarity_breakdown": similarity_breakdown,
            "confidence": self._compute_confidence(similarity_breakdown),
        }
    
    def _generate_summary(
        self,
        score: float,
        key_terms: List[str],
        breakdown: Dict[str, float],
    ) -> str:
        """Generate a natural language summary."""
        # Determine strength
        if score >= 0.8:
            strength = "highly"
        elif score >= 0.6:
            strength = "moderately"
        else:
            strength = "somewhat"
        
        # Build explanation
        if key_terms:
            terms_str = ", ".join(key_terms[:3])
            summary = f"This paper is {strength} relevant due to shared concepts: {terms_str}."
        else:
            summary = f"This paper is {strength} relevant based on semantic similarity."
        
        # Add breakdown info
        if breakdown.get("semantic", 0) > breakdown.get("keyword", 0):
            summary += " The match is primarily semantic rather than keyword-based."
        elif breakdown.get("keyword", 0) > breakdown.get("semantic", 0):
            summary += " The match is based on strong keyword overlap."
        
        return summary
    
    def _compute_confidence(self, breakdown: Dict[str, float]) -> str:
        """Compute confidence level of the explanation."""
        overall = breakdown.get("overall", 0)
        
        if overall >= 0.7:
            return "high"
        elif overall >= 0.4:
            return "medium"
        else:
            return "low"
    
    def batch_generate(
        self,
        recommendations: List[Dict],
    ) -> List[Dict]:
        """Generate explanations for multiple recommendations."""
        return [
            self.generate(
                query=rec.get("query", ""),
                recommended_title=rec.get("title", ""),
                similarity_score=rec.get("score", 0),
                key_terms=rec.get("key_terms", []),
                similarity_breakdown=rec.get("breakdown", {}),
            )
            for rec in recommendations
        ]
