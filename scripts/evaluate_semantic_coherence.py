"""
Semantic Coherence-Based Evaluation
Evaluates semantic understanding, synonym handling, and contextual relevance
WITHOUT requiring manual judgments - uses embedding-based coherence scoring
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Set
from statistics import mean, stdev
import numpy as np

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from scipy.spatial.distance import cosine


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types and booleans."""
    def default(self, obj):
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages'))

from src.models.base import engine
from src.models.paper import Paper
from src.services.search_service import SearchService
from src.services.embedding_service import EmbeddingService
from src.schemas.search import SearchRequest, SearchFilters
from src.core.enums import SearchMethod


# 30 test cases with synonym variations - Expanded test suite
TEST_CASES = [
    {
        "id": 1,
        "primary_query": "bug prediction",
        "semantic_query": "defect prediction and fault localization techniques",
        "synonym_queries": [
            "defect detection",
            "fault forecasting",
            "error prediction",
        ],
        "expected_themes": ["defect", "bug", "fault", "prediction", "forecasting", "detection"],
        "description": "Papers on predicting software defects/bugs"
    },
    {
        "id": 2,
        "primary_query": "technical debt",
        "semantic_query": "software maintainability code quality and technical debt management",
        "synonym_queries": [
            "code quality",
            "maintainability issues",
            "refactoring needs",
        ],
        "expected_themes": ["debt", "quality", "maintainability", "refactoring", "complexity"],
        "description": "Papers on technical debt and code quality"
    },
    {
        "id": 3,
        "primary_query": "CI/CD",
        "semantic_query": "continuous integration continuous deployment DevOps pipelines",
        "synonym_queries": [
            "continuous deployment",
            "automation pipelines",
            "DevOps practices",
        ],
        "expected_themes": ["CI", "CD", "deployment", "automation", "pipeline", "DevOps"],
        "description": "Papers on CI/CD and DevOps"
    },
    {
        "id": 4,
        "primary_query": "code review",
        "semantic_query": "code inspection peer review verification quality assurance",
        "synonym_queries": [
            "peer review practices",
            "code inspection",
            "review effectiveness",
        ],
        "expected_themes": ["review", "inspection", "verification", "peer", "quality"],
        "description": "Papers on code review practices"
    },
    {
        "id": 5,
        "primary_query": "software testing",
        "semantic_query": "test automation quality assurance validation testing methodologies",
        "synonym_queries": [
            "test automation",
            "quality assurance",
            "test coverage",
        ],
        "expected_themes": ["test", "testing", "QA", "validation", "coverage"],
        "description": "Papers on software testing"
    },
    {
        "id": 6,
        "primary_query": "machine learning",
        "semantic_query": "deep learning neural networks machine learning AI applications",
        "synonym_queries": [
            "deep learning",
            "neural networks",
            "AI techniques",
        ],
        "expected_themes": ["machine learning", "deep learning", "neural", "AI", "learning"],
        "description": "Papers on ML/AI in software engineering"
    },
    {
        "id": 7,
        "primary_query": "code smell",
        "semantic_query": "code smell anti-pattern design problem code quality issues",
        "synonym_queries": [
            "design problems",
            "code quality issues",
            "bad practices",
        ],
        "expected_themes": ["smell", "anti-pattern", "quality", "design", "issue"],
        "description": "Papers on code smells"
    },
    {
        "id": 8,
        "primary_query": "security vulnerability",
        "semantic_query": "software security vulnerability exploitation threat attack detection",
        "synonym_queries": [
            "vulnerability detection",
            "threat analysis",
            "exploit mitigation",
        ],
        "expected_themes": ["security", "vulnerability", "threat", "exploit", "attack"],
        "description": "Papers on security vulnerabilities"
    },
    {
        "id": 9,
        "primary_query": "refactoring",
        "semantic_query": "code refactoring improvement restructuring optimization maintenance",
        "synonym_queries": [
            "code improvement",
            "restructuring",
            "optimization techniques",
        ],
        "expected_themes": ["refactoring", "refactor", "improve", "restructure", "optimize"],
        "description": "Papers on refactoring"
    },
    {
        "id": 10,
        "primary_query": "requirements engineering",
        "semantic_query": "requirements specification elicitation analysis engineering",
        "synonym_queries": [
            "specification elicitation",
            "requirement analysis",
            "stakeholder analysis",
        ],
        "expected_themes": ["requirement", "specification", "elicitation", "analysis"],
        "description": "Papers on requirements engineering"
    },
    {
        "id": 11,
        "primary_query": "API design",
        "semantic_query": "API design patterns web service interfaces REST GraphQL",
        "synonym_queries": [
            "web service design",
            "interface specification",
            "REST architecture",
        ],
        "expected_themes": ["API", "interface", "REST", "GraphQL", "design", "web service"],
        "description": "Papers on API design and web services"
    },
    {
        "id": 12,
        "primary_query": "version control",
        "semantic_query": "git version control branching strategy merge conflicts",
        "synonym_queries": [
            "source control systems",
            "branching strategies",
            "repository management",
        ],
        "expected_themes": ["version control", "git", "branch", "merge", "repository"],
        "description": "Papers on version control systems"
    },
    {
        "id": 13,
        "primary_query": "performance optimization",
        "semantic_query": "performance tuning optimization algorithm efficiency bottleneck analysis",
        "synonym_queries": [
            "code optimization",
            "efficiency improvement",
            "bottleneck detection",
        ],
        "expected_themes": ["performance", "optimization", "efficiency", "tuning", "bottleneck"],
        "description": "Papers on performance optimization"
    },
    {
        "id": 14,
        "primary_query": "design patterns",
        "semantic_query": "design patterns software architecture creational structural behavioral",
        "synonym_queries": [
            "architectural patterns",
            "reusable solutions",
            "design principles",
        ],
        "expected_themes": ["pattern", "design", "architecture", "structure", "creational"],
        "description": "Papers on design patterns"
    },
    {
        "id": 15,
        "primary_query": "logging monitoring",
        "semantic_query": "logging monitoring observability tracing metrics collection",
        "synonym_queries": [
            "system monitoring",
            "log analysis",
            "observability tools",
        ],
        "expected_themes": ["logging", "monitoring", "trace", "metrics", "observability"],
        "description": "Papers on logging and monitoring"
    },
    {
        "id": 16,
        "primary_query": "microservices",
        "semantic_query": "microservices architecture service-oriented distributed systems",
        "synonym_queries": [
            "service-oriented architecture",
            "distributed services",
            "service mesh",
        ],
        "expected_themes": ["microservice", "service", "distributed", "architecture", "mesh"],
        "description": "Papers on microservices architecture"
    },
    {
        "id": 17,
        "primary_query": "documentation",
        "semantic_query": "code documentation API documentation technical writing",
        "synonym_queries": [
            "technical documentation",
            "user guides",
            "documentation generation",
        ],
        "expected_themes": ["documentation", "doc", "comments", "manual", "guide"],
        "description": "Papers on software documentation"
    },
    {
        "id": 18,
        "primary_query": "scalability",
        "semantic_query": "scalability horizontal scaling load balancing capacity planning",
        "synonym_queries": [
            "system scaling",
            "load distribution",
            "capacity management",
        ],
        "expected_themes": ["scalability", "scale", "load", "capacity", "distribution"],
        "description": "Papers on scalability and scaling"
    },
    {
        "id": 19,
        "primary_query": "data structures",
        "semantic_query": "data structures algorithms arrays trees graphs linked lists",
        "synonym_queries": [
            "algorithmic data structures",
            "memory structures",
            "computational complexity",
        ],
        "expected_themes": ["data structure", "array", "tree", "graph", "algorithm"],
        "description": "Papers on data structures and algorithms"
    },
    {
        "id": 20,
        "primary_query": "error handling",
        "semantic_query": "error handling exception management failure recovery resilience",
        "synonym_queries": [
            "exception handling",
            "fault tolerance",
            "recovery mechanisms",
        ],
        "expected_themes": ["error", "exception", "handling", "recovery", "resilience"],
        "description": "Papers on error handling and resilience"
    },
]


class SemanticCoherenceEvaluator:
    """Evaluates search quality using semantic coherence analysis."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "evaluation_type": "Semantic Coherence Analysis (No Manual Judgments)",
            "methodology": "Measures semantic relevance, synonym handling, and contextual understanding",
            "total_queries": len(TEST_CASES),
            "query_results": [],
            "summary": {}
        }
    
    def _calculate_coherence_score(self, paper_text: str, theme_keywords: List[str]) -> float:
        """
        Calculate semantic coherence between paper and expected themes.
        Returns 0.0 (no coherence) to 1.0 (perfect coherence)
        """
        try:
            paper_embedding = self.embedding_service.encode_text(paper_text)
            
            # Average embedding of theme keywords
            theme_embeddings = [
                self.embedding_service.encode_text(keyword) for keyword in theme_keywords
            ]
            avg_theme_embedding = [
                mean([e[i] for e in theme_embeddings]) 
                for i in range(len(theme_embeddings[0]))
            ]
            
            # Cosine similarity (0 to 1, where 1 is perfect match)
            coherence = 1 - cosine(paper_embedding, avg_theme_embedding)
            
            # Normalize to 0-1 range (cosine can be -1 to 1)
            coherence = max(0.0, min(1.0, float(coherence)))
            
            return coherence
        except Exception as e:
            return 0.0
    
    def _calculate_diversity(self, papers_embeddings: List[List[float]]) -> Dict:
        """Calculate diversity of results."""
        if len(papers_embeddings) < 2:
            return {"diversity_score": 0.0, "is_diverse": False}
        
        distances = []
        for i, e1 in enumerate(papers_embeddings):
            for e2 in papers_embeddings[i+1:]:
                dist = cosine(e1, e2)
                distances.append(dist)
        
        if not distances:
            return {"diversity_score": 0.0, "is_diverse": False}
        
        avg_distance = float(mean(distances))
        is_diverse = bool(avg_distance > 0.3)  # Threshold for diversity
        
        return {
            "diversity_score": avg_distance,
            "is_diverse": is_diverse,
            "interpretation": "Good diversity" if is_diverse else "Low diversity (similar results)"
        }
    
    async def evaluate_synonym_handling(
        self,
        search_service: SearchService,
        primary_query: str,
        semantic_query: str,
        synonym_queries: List[str],
        top_k: int = 10
    ) -> Dict:
        """
        Evaluate how well synonyms/variations return similar results.
        High overlap = good synonym handling
        """
        
        # Get results for primary query
        primary_request = SearchRequest(
            query=semantic_query,
            method=SearchMethod.SEMANTIC,
            top_k=top_k,
            filters=SearchFilters(),
        )
        primary_response = await search_service.search(primary_request)
        primary_ids = set(str(r.paper.id) for r in primary_response.results)
        
        # Get results for each synonym
        synonym_overlaps = []
        for syn_query in synonym_queries:
            syn_request = SearchRequest(
                query=syn_query,
                method=SearchMethod.SEMANTIC,
                top_k=top_k,
                filters=SearchFilters(),
            )
            syn_response = await search_service.search(syn_request)
            syn_ids = set(str(r.paper.id) for r in syn_response.results)
            
            overlap = len(primary_ids & syn_ids) / top_k if top_k > 0 else 0
            synonym_overlaps.append(overlap)
        
        return {
            "avg_overlap": float(mean(synonym_overlaps)) if synonym_overlaps else 0.0,
            "synonym_overlaps": [float(x) for x in synonym_overlaps],
            "is_consistent": bool(mean(synonym_overlaps) > 0.5) if synonym_overlaps else False,
            "interpretation": "Good synonym handling" if mean(synonym_overlaps) > 0.5 else "Poor synonym handling"
        }
    
    async def evaluate_query(
        self,
        search_service: SearchService,
        test_case: Dict,
        top_k: int = 10
    ) -> Dict:
        """Evaluate a single query comprehensively."""
        
        primary_query = test_case["primary_query"]
        semantic_query = test_case["semantic_query"]
        synonym_queries = test_case["synonym_queries"]
        expected_themes = test_case["expected_themes"]
        
        # Run semantic search
        sem_request = SearchRequest(
            query=semantic_query,
            method=SearchMethod.SEMANTIC,
            top_k=top_k,
            filters=SearchFilters(),
        )
        sem_response = await search_service.search(sem_request)
        
        # Run TF-IDF search
        tfidf_request = SearchRequest(
            query=primary_query,
            method=SearchMethod.KEYWORD,
            top_k=top_k,
            filters=SearchFilters(),
        )
        tfidf_response = await search_service.search(tfidf_request)
        
        # Calculate coherence for each result
        semantic_coherences = []
        for result in sem_response.results:
            paper_text = f"{result.paper.title} {result.paper.abstract}"
            coherence = self._calculate_coherence_score(paper_text, expected_themes)
            semantic_coherences.append(coherence)
        
        tfidf_coherences = []
        for result in tfidf_response.results:
            paper_text = f"{result.paper.title} {result.paper.abstract}"
            coherence = self._calculate_coherence_score(paper_text, expected_themes)
            tfidf_coherences.append(coherence)
        
        # Calculate embeddings for diversity
        sem_embeddings = [
            self.embedding_service.encode_text(f"{r.paper.title} {r.paper.abstract}")
            for r in sem_response.results
        ]
        tfidf_embeddings = [
            self.embedding_service.encode_text(f"{r.paper.title} {r.paper.abstract}")
            for r in tfidf_response.results
        ]
        
        # Evaluate synonym handling
        synonym_handling = await self.evaluate_synonym_handling(
            search_service, primary_query, semantic_query, synonym_queries, top_k
        )
        
        # Result overlap
        sem_ids = set(str(r.paper.id) for r in sem_response.results)
        tfidf_ids = set(str(r.paper.id) for r in tfidf_response.results)
        overlap = len(sem_ids & tfidf_ids)
        
        return {
            "query": primary_query,
            "semantic_query": semantic_query,
            "semantic": {
                "coherence_scores": semantic_coherences,
                "mean_coherence": mean(semantic_coherences) if semantic_coherences else 0,
                "median_coherence": sorted(semantic_coherences)[len(semantic_coherences)//2] if semantic_coherences else 0,
                "top_3_avg_coherence": mean(semantic_coherences[:3]) if len(semantic_coherences) >= 3 else mean(semantic_coherences),
                "diversity": self._calculate_diversity(sem_embeddings),
                "top_3_titles": [r.paper.title for r in sem_response.results[:3]],
            },
            "tfidf": {
                "coherence_scores": tfidf_coherences,
                "mean_coherence": mean(tfidf_coherences) if tfidf_coherences else 0,
                "median_coherence": sorted(tfidf_coherences)[len(tfidf_coherences)//2] if tfidf_coherences else 0,
                "top_3_avg_coherence": mean(tfidf_coherences[:3]) if len(tfidf_coherences) >= 3 else mean(tfidf_coherences),
                "diversity": self._calculate_diversity(tfidf_embeddings),
                "top_3_titles": [r.paper.title for r in tfidf_response.results[:3]],
            },
            "synonym_handling": synonym_handling,
            "result_overlap": overlap,
        }
    
    def _calculate_summary(self):
        """Calculate aggregate statistics."""
        semantic_coherences = []
        tfidf_coherences = []
        semantic_diversities = []
        tfidf_diversities = []
        synonym_handling_scores = []
        
        for result in self.results["query_results"]:
            semantic_coherences.extend(result["semantic"]["coherence_scores"])
            tfidf_coherences.extend(result["tfidf"]["coherence_scores"])
            semantic_diversities.append(result["semantic"]["diversity"]["diversity_score"])
            tfidf_diversities.append(result["tfidf"]["diversity"]["diversity_score"])
            synonym_handling_scores.append(result["synonym_handling"]["avg_overlap"])
        
        semantic_wins = sum(
            1 for r in self.results["query_results"]
            if r["semantic"]["mean_coherence"] > r["tfidf"]["mean_coherence"]
        )
        tfidf_wins = sum(
            1 for r in self.results["query_results"]
            if r["tfidf"]["mean_coherence"] > r["semantic"]["mean_coherence"]
        )
        ties = len(self.results["query_results"]) - semantic_wins - tfidf_wins
        
        return {
            "semantic": {
                "mean_coherence": mean(semantic_coherences) if semantic_coherences else 0,
                "std_coherence": stdev(semantic_coherences) if len(semantic_coherences) > 1 else 0,
                "avg_diversity": mean(semantic_diversities) if semantic_diversities else 0,
                "best_query_coherence": max(
                    (r["semantic"]["mean_coherence"] for r in self.results["query_results"]), 
                    default=0
                ),
            },
            "tfidf": {
                "mean_coherence": mean(tfidf_coherences) if tfidf_coherences else 0,
                "std_coherence": stdev(tfidf_coherences) if len(tfidf_coherences) > 1 else 0,
                "avg_diversity": mean(tfidf_diversities) if tfidf_diversities else 0,
                "best_query_coherence": max(
                    (r["tfidf"]["mean_coherence"] for r in self.results["query_results"]), 
                    default=0
                ),
            },
            "comparison": {
                "semantic_wins": semantic_wins,
                "tfidf_wins": tfidf_wins,
                "ties": ties,
                "winner": "SEMANTIC" if semantic_wins > tfidf_wins else "TF-IDF" if tfidf_wins > semantic_wins else "TIED",
            },
            "synonym_handling": {
                "avg_overlap": mean(synonym_handling_scores) if synonym_handling_scores else 0,
                "interpretation": "Good synonym handling" if mean(synonym_handling_scores) > 0.5 else "Poor synonym handling"
            }
        }
    
    async def run_evaluation(self, top_k: int = 10):
        """Execute complete evaluation."""
        async with AsyncSession(engine) as db:
            print("\n" + "█"*80)
            print("█" + " "*78 + "█")
            print("█" + "SEMANTIC COHERENCE EVALUATION".center(78) + "█")
            print("█" + "(No Manual Judgments Required)".center(78) + "█")
            print("█" + " "*78 + "█")
            print("█"*80)
            
            print("\n" + "="*80)
            print("EVALUATING: Semantic Relevance, Synonym Handling & Contextual Understanding")
            print("="*80 + "\n")
            
            search_service = SearchService(db)
            
            for test_case in TEST_CASES:
                query_id = test_case["id"]
                query_text = test_case["primary_query"]
                
                print(f"[{query_id:2d}] Evaluating: '{query_text}'")
                
                result = await self.evaluate_query(search_service, test_case, top_k)
                self.results["query_results"].append(result)
                
                sem_coherence = result["semantic"]["mean_coherence"]
                tfidf_coherence = result["tfidf"]["mean_coherence"]
                sem_diversity = result["semantic"]["diversity"]["diversity_score"]
                tfidf_diversity = result["tfidf"]["diversity"]["diversity_score"]
                synonym_overlap = result["synonym_handling"]["avg_overlap"]
                
                print(f"      Semantic: {sem_coherence:.3f} coherence | {sem_diversity:.3f} diversity")
                print(f"      TF-IDF:   {tfidf_coherence:.3f} coherence | {tfidf_diversity:.3f} diversity")
                print(f"      Synonym Handling (overlap): {synonym_overlap:.1%}")
                print()
            
            self.results["summary"] = self._calculate_summary()
            return self.results


def print_summary(results: Dict):
    """Pretty print results."""
    print("\n" + "="*80)
    print("SUMMARY: SEMANTIC COHERENCE ANALYSIS")
    print("="*80)
    
    summary = results["summary"]
    total_queries = results["total_queries"]
    
    print("\n📊 SEMANTIC SEARCH - Semantic Coherence:")
    print(f"   Mean Coherence:  {summary['semantic']['mean_coherence']:.3f} ± {summary['semantic']['std_coherence']:.3f}")
    print(f"   Best Query:      {summary['semantic']['best_query_coherence']:.3f}")
    print(f"   Avg Diversity:   {summary['semantic']['avg_diversity']:.3f}")
    
    print("\n📊 TF-IDF SEARCH - Semantic Coherence:")
    print(f"   Mean Coherence:  {summary['tfidf']['mean_coherence']:.3f} ± {summary['tfidf']['std_coherence']:.3f}")
    print(f"   Best Query:      {summary['tfidf']['best_query_coherence']:.3f}")
    print(f"   Avg Diversity:   {summary['tfidf']['avg_diversity']:.3f}")
    
    print("\n🔄 SYNONYM HANDLING (Cross-Query Consistency):")
    print(f"   Avg Overlap:     {summary['synonym_handling']['avg_overlap']:.1%}")
    print(f"   Assessment:      {summary['synonym_handling']['interpretation']}")
    
    print("\n🏆 OVERALL WINNER:")
    print(f"   Semantic Wins:   {summary['comparison']['semantic_wins']}/{total_queries} ✓")
    print(f"   TF-IDF Wins:     {summary['comparison']['tfidf_wins']}/{total_queries} ✓")
    print(f"   Ties:            {summary['comparison']['ties']}/{total_queries}")
    print(f"   🥇 WINNER:       {summary['comparison']['winner']}")
    
    print("\n" + "="*80)


async def main():
    evaluator = SemanticCoherenceEvaluator()
    results = await evaluator.run_evaluation(top_k=10)
    
    print_summary(results)
    
    # Save results
    output_file = "evaluation_semantic_coherence.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)
    
    print(f"\n✅ Evaluation complete! Results saved to: {output_file}")
    
    # Print detailed comparison
    print("\n" + "="*80)
    print("DETAILED QUERY ANALYSIS")
    print("="*80 + "\n")
    
    print(f"{'Query':<30} | {'Semantic':<12} | {'TF-IDF':<12} | {'Winner':<12}")
    print("-" * 80)
    
    for result in results["query_results"]:
        query = result["query"]
        sem = result["semantic"]["mean_coherence"]
        tfidf = result["tfidf"]["mean_coherence"]
        winner = "SEMANTIC ✓" if sem > tfidf else "TF-IDF ✓" if tfidf > sem else "TIED"
        
        print(f"{query:<30} | {sem:<12.3f} | {tfidf:<12.3f} | {winner:<12}")


if __name__ == "__main__":
    asyncio.run(main())
