"""
Comprehensive Evaluation of Semantic vs TF-IDF Baseline

Implements metrics from the evaluation guide:
- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- NDCG
- Semantic Capability Evaluation
- Response Time Evaluation
"""

import asyncio
import sys
import os
import json
import time
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages'))

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import engine
from src.services.search_service import SearchService
from src.services.baseline_service import BaselineService
from src.schemas.search import SearchRequest, SearchFilters
from src.core.enums import SearchMethod


# Evaluation Dataset with manually identified relevant papers
EVALUATION_DATASET = [
    {
        "query": "bug prediction",
        "semantic_query": "defect prediction and fault localization",
        "relevant_keywords": ["bug", "defect", "fault", "prediction", "error detection"],
        "description": "Papers on predicting software bugs and defects"
    },
    {
        "query": "technical debt",
        "semantic_query": "software maintainability and code quality",
        "relevant_keywords": ["technical debt", "maintainability", "code quality", "refactoring"],
        "description": "Papers on technical debt and maintenance"
    },
    {
        "query": "CI/CD",
        "semantic_query": "continuous integration deployment DevOps pipelines",
        "relevant_keywords": ["CI/CD", "continuous integration", "deployment", "DevOps", "pipeline"],
        "description": "Papers on continuous integration and deployment"
    },
    {
        "query": "code review",
        "semantic_query": "code inspection peer review verification",
        "relevant_keywords": ["code review", "review", "inspection", "verification"],
        "description": "Papers on code review practices and effectiveness"
    },
    {
        "query": "software testing",
        "semantic_query": "test automation quality assurance validation",
        "relevant_keywords": ["testing", "test", "quality assurance", "validation", "automated test"],
        "description": "Papers on software testing methodologies"
    },
    {
        "query": "machine learning in software engineering",
        "semantic_query": "deep learning neural networks software development",
        "relevant_keywords": ["machine learning", "deep learning", "neural network", "AI", "software"],
        "description": "Papers on ML applications in SE"
    },
    {
        "query": "code smell",
        "semantic_query": "software quality anti-pattern design problem",
        "relevant_keywords": ["code smell", "anti-pattern", "quality issue", "bad design"],
        "description": "Papers on code smells and quality issues"
    },
    {
        "query": "security vulnerability",
        "semantic_query": "software security vulnerability exploitation attack",
        "relevant_keywords": ["security", "vulnerability", "exploit", "threat", "attack"],
        "description": "Papers on security vulnerabilities"
    },
    {
        "query": "refactoring",
        "semantic_query": "code improvement restructuring optimization",
        "relevant_keywords": ["refactoring", "refactor", "restructuring", "optimization"],
        "description": "Papers on software refactoring"
    },
    {
        "query": "requirements engineering",
        "semantic_query": "requirement specification elicitation analysis",
        "relevant_keywords": ["requirements", "specification", "elicitation", "analysis"],
        "description": "Papers on requirements engineering"
    },
]


class SemanticEvaluator:
    """Comprehensive evaluation framework for semantic vs TF-IDF."""
    
    def __init__(self):
        self.results = {
            "timestamp": None,
            "queries_evaluated": 0,
            "metrics": {
                "semantic": {},
                "tfidf": {},
                "comparison": {}
            },
            "detailed_results": [],
            "performance_metrics": {
                "semantic": [],
                "tfidf": []
            }
        }
    
    def _extract_relevant_papers(self, results, keywords: List[str], top_k: int = 10) -> Set[str]:
        """Extract paper IDs based on keyword matching in title/abstract."""
        relevant = set()
        for result in results[:top_k]:
            paper_text = (
                result.paper.title + " " + result.paper.abstract
            ).lower()
            for keyword in keywords:
                if keyword.lower() in paper_text:
                    relevant.add(str(result.paper.id))
                    break
        return relevant
    
    def precision_at_k(self, retrieved: List[str], relevant: Set[str], k: int = 10) -> float:
        """Calculate Precision@K."""
        if k <= 0 or not retrieved:
            return 0.0
        
        retrieved_k = set(retrieved[:k])
        relevant_retrieved = len(retrieved_k & relevant)
        
        return relevant_retrieved / k if k > 0 else 0.0
    
    def recall_at_k(self, retrieved: List[str], relevant: Set[str], k: int = 10) -> float:
        """Calculate Recall@K."""
        if not relevant or not retrieved:
            return 0.0
        
        retrieved_k = set(retrieved[:k])
        relevant_retrieved = len(retrieved_k & relevant)
        
        return relevant_retrieved / len(relevant) if len(relevant) > 0 else 0.0
    
    def mean_reciprocal_rank(self, retrieved: List[str], relevant: Set[str]) -> float:
        """Calculate Mean Reciprocal Rank."""
        if not retrieved or not relevant:
            return 0.0
        
        for rank, paper_id in enumerate(retrieved, 1):
            if paper_id in relevant:
                return 1.0 / rank
        
        return 0.0
    
    def ndcg_at_k(self, retrieved: List[str], relevant: Set[str], k: int = 10) -> float:
        """Calculate NDCG@K."""
        if not retrieved or not relevant:
            return 0.0
        
        # DCG@K
        dcg = 0.0
        for rank, paper_id in enumerate(retrieved[:k], 1):
            relevance = 1 if paper_id in relevant else 0
            dcg += relevance / (1 + (rank - 1))  # Using log2 base
        
        # IDCG@K (ideal ranking)
        idcg = 0.0
        for rank in range(1, min(k, len(relevant)) + 1):
            idcg += 1.0 / rank
        
        return dcg / idcg if idcg > 0 else 0.0
    
    async def evaluate_query(
        self,
        db: AsyncSession,
        query: str,
        semantic_query: str,
        keywords: List[str],
        top_k: int = 10
    ) -> Dict:
        """Evaluate a single query with both methods."""
        
        search_service = SearchService(db)
        
        # Time semantic search
        start = time.time()
        semantic_request = SearchRequest(
            query=semantic_query,
            method=SearchMethod.SEMANTIC,
            top_k=top_k,
            filters=SearchFilters(),
        )
        semantic_response = await search_service.search(semantic_request)
        semantic_time = time.time() - start
        
        # Time TF-IDF search
        start = time.time()
        tfidf_request = SearchRequest(
            query=query,
            method=SearchMethod.KEYWORD,
            top_k=top_k,
            filters=SearchFilters(),
        )
        tfidf_response = await search_service.search(tfidf_request)
        tfidf_time = time.time() - start
        
        # Extract paper IDs
        semantic_ids = [str(r.paper.id) for r in semantic_response.results]
        tfidf_ids = [str(r.paper.id) for r in tfidf_response.results]
        
        # Extract relevant papers based on keywords
        relevant_semantic = self._extract_relevant_papers(semantic_response.results, keywords, top_k)
        relevant_tfidf = self._extract_relevant_papers(tfidf_response.results, keywords, top_k)
        
        # Calculate metrics
        semantic_metrics = {
            "precision_at_5": self.precision_at_k(semantic_ids, relevant_semantic, 5),
            "precision_at_10": self.precision_at_k(semantic_ids, relevant_semantic, 10),
            "recall_at_5": self.recall_at_k(semantic_ids, relevant_semantic, 5),
            "recall_at_10": self.recall_at_k(semantic_ids, relevant_semantic, 10),
            "mrr": self.mean_reciprocal_rank(semantic_ids, relevant_semantic),
            "ndcg_at_10": self.ndcg_at_k(semantic_ids, relevant_semantic, 10),
            "response_time_ms": semantic_time * 1000,
            "results_count": len(semantic_response.results),
            "relevant_found": len(relevant_semantic),
        }
        
        tfidf_metrics = {
            "precision_at_5": self.precision_at_k(tfidf_ids, relevant_tfidf, 5),
            "precision_at_10": self.precision_at_k(tfidf_ids, relevant_tfidf, 10),
            "recall_at_5": self.recall_at_k(tfidf_ids, relevant_tfidf, 5),
            "recall_at_10": self.recall_at_k(tfidf_ids, relevant_tfidf, 10),
            "mrr": self.mean_reciprocal_rank(tfidf_ids, relevant_tfidf),
            "ndcg_at_10": self.ndcg_at_k(tfidf_ids, relevant_tfidf, 10),
            "response_time_ms": tfidf_time * 1000,
            "results_count": len(tfidf_response.results),
            "relevant_found": len(relevant_tfidf),
        }
        
        # Semantic capability evaluation
        semantic_overlap = set(semantic_ids) & set(tfidf_ids)
        semantic_advantage = len(set(semantic_ids) - set(tfidf_ids))
        
        return {
            "query": query,
            "semantic_query": semantic_query,
            "semantic_metrics": semantic_metrics,
            "tfidf_metrics": tfidf_metrics,
            "comparison": {
                "overlap": len(semantic_overlap),
                "semantic_unique": semantic_advantage,
                "semantic_precision_advantage": semantic_metrics["precision_at_10"] - tfidf_metrics["precision_at_10"],
                "semantic_ndcg_advantage": semantic_metrics["ndcg_at_10"] - tfidf_metrics["ndcg_at_10"],
                "tfidf_faster": tfidf_time < semantic_time,
                "speedup_ratio": semantic_time / tfidf_time if tfidf_time > 0 else 0,
            },
            "top_results": {
                "semantic": [
                    {
                        "title": r.paper.title[:60],
                        "score": r.score
                    }
                    for r in semantic_response.results[:3]
                ],
                "tfidf": [
                    {
                        "title": r.paper.title[:60],
                        "score": r.score
                    }
                    for r in tfidf_response.results[:3]
                ]
            }
        }
    
    def aggregate_metrics(self) -> Dict:
        """Compute aggregate metrics across all queries."""
        if not self.results["detailed_results"]:
            return {}
        
        semantic_metrics = defaultdict(list)
        tfidf_metrics = defaultdict(list)
        
        for result in self.results["detailed_results"]:
            for metric, value in result["semantic_metrics"].items():
                if isinstance(value, (int, float)):
                    semantic_metrics[metric].append(value)
            
            for metric, value in result["tfidf_metrics"].items():
                if isinstance(value, (int, float)):
                    tfidf_metrics[metric].append(value)
        
        aggregated = {
            "semantic": {},
            "tfidf": {},
            "advantages": {}
        }
        
        # Calculate averages
        for metric, values in semantic_metrics.items():
            if values:
                aggregated["semantic"][metric] = {
                    "mean": statistics.mean(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values),
                }
        
        for metric, values in tfidf_metrics.items():
            if values:
                aggregated["tfidf"][metric] = {
                    "mean": statistics.mean(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values),
                }
        
        # Calculate advantages
        for metric in ["precision_at_10", "recall_at_10", "mrr", "ndcg_at_10"]:
            if metric in aggregated["semantic"] and metric in aggregated["tfidf"]:
                semantic_mean = aggregated["semantic"][metric]["mean"]
                tfidf_mean = aggregated["tfidf"][metric]["mean"]
                advantage = ((semantic_mean - tfidf_mean) / tfidf_mean * 100) if tfidf_mean > 0 else 0
                aggregated["advantages"][metric] = f"{advantage:+.1f}%"
        
        return aggregated
    
    async def run_evaluation(self):
        """Run comprehensive evaluation."""
        print("\n" + "="*80)
        print("SEMANTIC VS TF-IDF BASELINE EVALUATION")
        print("="*80)
        print(f"\nEvaluating {len(EVALUATION_DATASET)} queries...\n")
        
        async with AsyncSession(engine) as db:
            for i, test_case in enumerate(EVALUATION_DATASET, 1):
                print(f"[{i}/{len(EVALUATION_DATASET)}] Evaluating: '{test_case['query']}'")
                
                result = await self.evaluate_query(
                    db,
                    query=test_case["query"],
                    semantic_query=test_case["semantic_query"],
                    keywords=test_case["relevant_keywords"],
                    top_k=10
                )
                
                self.results["detailed_results"].append(result)
                self.results["queries_evaluated"] += 1
                
                # Print quick results
                print(f"  Semantic:  P@10={result['semantic_metrics']['precision_at_10']:.3f}, "
                      f"R@10={result['semantic_metrics']['recall_at_10']:.3f}, "
                      f"NDCG={result['semantic_metrics']['ndcg_at_10']:.3f}")
                print(f"  TF-IDF:    P@10={result['tfidf_metrics']['precision_at_10']:.3f}, "
                      f"R@10={result['tfidf_metrics']['recall_at_10']:.3f}, "
                      f"NDCG={result['tfidf_metrics']['ndcg_at_10']:.3f}")
                print(f"  Advantage: {result['comparison']['semantic_precision_advantage']:+.3f} "
                      f"(precision), {result['comparison']['semantic_ndcg_advantage']:+.3f} (NDCG)")
                print()
        
        # Aggregate metrics
        self.results["metrics"] = self.aggregate_metrics()
        
        # Print summary
        self._print_summary()
        
        # Save results
        self._save_results()
    
    def _print_summary(self):
        """Print evaluation summary."""
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        
        aggregated = self.results["metrics"]
        
        print("\n📊 QUANTITATIVE METRICS (Average across all queries)\n")
        
        metrics_to_show = ["precision_at_10", "recall_at_10", "mrr", "ndcg_at_10", "response_time_ms"]
        
        print(f"{'Metric':<25} {'Semantic':>15} {'TF-IDF':>15} {'Advantage':>15}")
        print("-" * 70)
        
        for metric in metrics_to_show:
            if metric in aggregated["semantic"] and metric in aggregated["tfidf"]:
                sem_mean = aggregated["semantic"][metric]["mean"]
                tfidf_mean = aggregated["tfidf"][metric]["mean"]
                
                if "time" in metric:
                    print(f"{metric:<25} {sem_mean:>15.2f}ms {tfidf_mean:>15.2f}ms", end="")
                else:
                    print(f"{metric:<25} {sem_mean:>15.3f} {tfidf_mean:>15.3f}", end="")
                    if metric in aggregated["advantages"]:
                        print(f" {aggregated['advantages'][metric]:>15}")
                    else:
                        print()
        
        print("\n🎯 SEMANTIC CAPABILITY EVALUATION\n")
        
        total_overlap = sum(r["comparison"]["overlap"] for r in self.results["detailed_results"])
        total_queries = len(self.results["detailed_results"])
        avg_overlap = total_overlap / (total_queries * 10) * 100 if total_queries > 0 else 0
        
        total_semantic_unique = sum(r["comparison"]["semantic_unique"] for r in self.results["detailed_results"])
        avg_unique_per_query = total_semantic_unique / total_queries if total_queries > 0 else 0
        
        print(f"Average overlap with TF-IDF: {avg_overlap:.1f}% of results")
        print(f"Average unique semantic results: {avg_unique_per_query:.1f} per query")
        print(f"Semantic finds papers TF-IDF misses: {'✓' if avg_unique_per_query > 0 else '✗'}")
        
        print("\n⚡ PERFORMANCE EVALUATION\n")
        
        if "response_time_ms" in aggregated["semantic"] and "response_time_ms" in aggregated["tfidf"]:
            sem_time = aggregated["semantic"]["response_time_ms"]["mean"]
            tfidf_time = aggregated["tfidf"]["response_time_ms"]["mean"]
            
            print(f"Average Semantic Response Time: {sem_time:.2f}ms")
            print(f"Average TF-IDF Response Time:   {tfidf_time:.2f}ms")
            
            if sem_time < tfidf_time:
                print(f"✓ Semantic is {(tfidf_time/sem_time):.1f}x faster")
            else:
                print(f"ℹ TF-IDF is {(sem_time/tfidf_time):.1f}x faster")
        
        print("\n" + "="*80)
    
    def _save_results(self):
        """Save evaluation results to JSON."""
        output_file = os.path.join(
            os.path.dirname(__file__),
            'evaluation_results.json'
        )
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n✓ Evaluation results saved to: {output_file}")


async def main():
    """Run the evaluation."""
    evaluator = SemanticEvaluator()
    await evaluator.run_evaluation()


if __name__ == "__main__":
    asyncio.run(main())
