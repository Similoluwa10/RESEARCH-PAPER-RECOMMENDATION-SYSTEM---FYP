"""
query_processor.py - Semantic Query Processing

Improves query understanding through expansion, rewriting, and domain-aware processing.
"""

import re
from typing import List, Tuple


class SEDomainExpander:
    """Expands software engineering queries with domain terminology."""
    
    # Domain-specific synonyms and related terms
    DOMAIN_EXPANSIONS = {
        "bug": ["defect", "fault", "error", "issue", "failure", "anomaly"],
        "prediction": ["forecasting", "prediction", "anticipation", "detection"],
        "technical debt": ["code quality", "maintainability", "complexity", "technical burden"],
        "ci/cd": ["continuous integration", "continuous deployment", "automation", "pipeline"],
        "code review": ["peer review", "code inspection", "verification", "quality assurance"],
        "testing": ["test", "qa", "quality assurance", "validation", "verification"],
        "machine learning": ["ml", "deep learning", "neural network", "ai", "learning"],
        "code smell": ["code quality", "bad practice", "design problem", "anti-pattern"],
        "security": ["vulnerability", "security", "threat", "exploit", "privacy"],
        "refactoring": ["refactor", "restructuring", "optimization", "improvement"],
        "requirements": ["specification", "requirement", "elicitation", "analysis"],
    }
    
    # Domain context terms that strengthen queries
    DOMAIN_CONTEXT = {
        "bug prediction": "defect forecasting machine learning empirical study",
        "technical debt": "code maintainability quality metrics complexity",
        "ci/cd": "build automation testing deployment pipeline DevOps",
        "code review": "quality assurance peer review inspection verification",
        "software testing": "test automation coverage quality validation",
        "machine learning": "deep learning classification prediction model training",
        "code smell": "design pattern quality metric detection",
        "security vulnerability": "threat detection exploit mitigation patch",
        "refactoring": "code restructuring improvement optimization maintenance",
        "requirements engineering": "specification elicitation stakeholder analysis",
    }
    
    @staticmethod
    def expand_query(query: str) -> str:
        """
        Expand a query with domain-specific synonyms.
        
        Args:
            query: Original search query
            
        Returns:
            Expanded query with related domain terms
        """
        expanded = query.lower()
        
        # Add domain context if available
        for key, context in SEDomainExpander.DOMAIN_CONTEXT.items():
            if key in expanded:
                expanded = f"{query} {context}"
                return expanded
        
        return query
    
    @staticmethod
    def rewrite_query(query: str) -> str:
        """
        Rewrite query to better capture semantic intent.
        
        Converts short queries to more descriptive form.
        """
        query_lower = query.lower()
        
        # Query rewriting patterns for SE domain
        rewrites = {
            "bug prediction": "predicting software bugs defects using machine learning",
            "technical debt": "understanding software technical debt maintainability and code quality",
            "ci/cd": "continuous integration deployment automation software pipeline",
            "code review": "code review process quality assurance peer review",
            "software testing": "software testing techniques automation quality assurance",
            "machine learning in software engineering": "applying machine learning deep learning to software engineering",
            "code smell": "detecting code smells bad practices quality issues",
            "security vulnerability": "software security vulnerabilities threats exploitation",
            "refactoring": "code refactoring restructuring optimization improvement",
            "requirements engineering": "requirements engineering specification elicitation",
        }
        
        for key, rewrite in rewrites.items():
            if key in query_lower:
                return rewrite
        
        return query


class QueryProcessor:
    """Main query processor combining expansion and rewriting."""
    
    def __init__(self):
        self.expander = SEDomainExpander()
    
    def process_for_semantic_search(self, query: str) -> Tuple[str, str]:
        """
        Process query for semantic search.
        
        Returns:
            Tuple of (expanded_query, rewritten_query)
        """
        # Expand with domain terms
        expanded = self.expander.expand_query(query)
        
        # Rewrite for semantic meaning
        rewritten = self.expander.rewrite_query(query)
        
        return expanded, rewritten
    
    def process_batch(self, queries: List[str]) -> List[Tuple[str, str]]:
        """Process multiple queries."""
        return [self.process_for_semantic_search(q) for q in queries]
