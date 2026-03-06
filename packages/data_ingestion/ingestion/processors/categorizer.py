"""
categorizer.py - Paper Categorizer

Categorizes papers into Software Engineering research domains.
Uses the shared SE_DOMAINS constants for consistency.
"""

import logging
import re
from typing import Dict, List, Tuple

from ingestion.clients.base import PaperData


# SE research domains with scoring keywords
# Aligned with packages/shared/constants/domains.py
SE_CATEGORY_KEYWORDS: Dict[str, Dict] = {
    "Software Testing": {
        "keywords": [
            "testing",
            "test case",
            "unit test",
            "integration test",
            "regression",
            "test automation",
            "mutation testing",
            "metamorphic testing",
            "test generation",
        ],
        "score_weight": 1.0,
    },
    "Software Maintenance": {
        "keywords": [
            "maintenance",
            "refactoring",
            "technical debt",
            "code smell",
            "legacy",
            "code quality",
        ],
        "score_weight": 1.0,
    },
    "Software Security": {
        "keywords": [
            "security",
            "vulnerability",
            "malware",
            "authentication",
            "encryption",
            "secure coding",
        ],
        "score_weight": 1.0,
    },
    "Machine Learning for SE": {
        "keywords": [
            "machine learning",
            "deep learning",
            "neural network",
            "AI",
            "prediction model",
            "code embedding",
        ],
        "score_weight": 1.0,
    },
    "Code Review": {
        "keywords": [
            "code review",
            "peer review",
            "inspection",
            "quality assurance",
            "pull request",
        ],
        "score_weight": 1.0,
    },
    "Requirements Engineering": {
        "keywords": [
            "requirements",
            "specification",
            "user story",
            "use case",
            "elicitation",
            "traceability",
        ],
        "score_weight": 1.0,
    },
    "Software Architecture": {
        "keywords": [
            "architecture",
            "design pattern",
            "microservices",
            "monolith",
            "architectural",
            "system design",
        ],
        "score_weight": 1.0,
    },
    "DevOps & CI/CD": {
        "keywords": [
            "devops",
            "continuous integration",
            "continuous deployment",
            "docker",
            "kubernetes",
            "agile",
            "scrum",
        ],
        "score_weight": 1.0,
    },
    "Program Analysis": {
        "keywords": [
            "static analysis",
            "dynamic analysis",
            "symbolic execution",
            "program slicing",
            "code analysis",
            "data flow",
        ],
        "score_weight": 1.0,
    },
    "Software Evolution": {
        "keywords": [
            "evolution",
            "versioning",
            "changelog",
            "migration",
            "software history",
        ],
        "score_weight": 1.0,
    },
}


class LoggerMixin:
    """Mixin class to add logging capability."""
    
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)


class PaperCategorizer(LoggerMixin):
    """
    Categorize papers by Software Engineering research domain.
    
    Uses keyword matching on title and abstract to assign
    papers to the most relevant SE category.
    """
    
    def __init__(self, categories: Dict[str, Dict] = None):
        """
        Initialize categorizer.
        
        Args:
            categories: Optional custom category definitions.
                        Defaults to SE_CATEGORY_KEYWORDS.
        """
        self.categories = categories or SE_CATEGORY_KEYWORDS
    
    @property
    def category_names(self) -> List[str]:
        """Get list of all category names."""
        return list(self.categories.keys())
    
    def categorize(self, paper: PaperData) -> str:
        """
        Categorize a single paper based on title and abstract.
        
        Args:
            paper: PaperData object to categorize
            
        Returns:
            Category name or 'Other' if no strong match
        """
        text = f"{paper.title} {paper.abstract}".lower()
        scores: Dict[str, float] = {}
        
        for category, config in self.categories.items():
            score = 0.0
            for keyword in config["keywords"]:
                # Count keyword occurrences (whole word matching)
                pattern = rf"\b{re.escape(keyword)}\b"
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * config["score_weight"]
            
            scores[category] = score
        
        # Return category with highest score
        best_category = max(scores, key=scores.get)
        if scores[best_category] > 0:
            return best_category
        
        return "Other"
    
    def categorize_papers(
        self,
        papers: List[PaperData],
    ) -> List[Tuple[PaperData, str]]:
        """
        Categorize multiple papers.
        
        Args:
            papers: List of PaperData objects
            
        Returns:
            List of tuples: (paper, category)
        """
        results = [(paper, self.categorize(paper)) for paper in papers]
        
        # Log category distribution
        category_counts: Dict[str, int] = {}
        for _, category in results:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        self.logger.info("Category distribution:")
        for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            self.logger.info(f"  {category}: {count}")
        
        return results
