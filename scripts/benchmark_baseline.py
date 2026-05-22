"""
benchmark_baseline.py - Baseline Benchmarking Script

Evaluates TF-IDF baseline performance against semantic search.
Provides metrics for comparison and evaluation.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages'))

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import engine
from src.services.search_service import SearchService
from src.services.baseline_service import BaselineService
from src.schemas.search import SearchRequest
from src.core.enums import SearchMethod


class BaselineBenchmark:
    """Benchmark TF-IDF baseline against semantic search."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": [],
            "summary": {},
        }
    
    async def run_comparison(
        self,
        query: str,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Run semantic vs baseline comparison for a query.
        
        Args:
            query: Test query
            top_k: Number of results to compare
            
        Returns:
            Comparison results
        """
        async with AsyncSession(engine) as session:
            service = SearchService(session)
            
            # Semantic search
            semantic_request = SearchRequest(
                query=query,
                method=SearchMethod.SEMANTIC,
                top_k=top_k,
            )
            semantic_results = await service.search(semantic_request)
            
            # TF-IDF search
            tfidf_request = SearchRequest(
                query=query,
                method=SearchMethod.KEYWORD,
                top_k=top_k,
            )
            tfidf_results = await service.search(tfidf_request)
            
            # Extract paper IDs and scores
            semantic_ids = [r["paper"]["id"] for r in semantic_results.results]
            tfidf_ids = [r["paper"]["id"] for r in tfidf_results.results]
            
            semantic_scores = [r["score"] for r in semantic_results.results]
            tfidf_scores = [r["score"] for r in tfidf_results.results]
            
            # Calculate overlap
            overlap = set(semantic_ids) & set(tfidf_ids)
            overlap_pct = (len(overlap) / top_k) * 100 if top_k > 0 else 0
            
            return {
                "query": query,
                "top_k": top_k,
                "semantic": {
                    "results_count": len(semantic_results.results),
                    "ids": semantic_ids,
                    "scores": semantic_scores,
                    "avg_score": sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0,
                },
                "tfidf": {
                    "results_count": len(tfidf_results.results),
                    "ids": tfidf_ids,
                    "scores": tfidf_scores,
                    "avg_score": sum(tfidf_scores) / len(tfidf_scores) if tfidf_scores else 0,
                },
                "overlap": {
                    "count": len(overlap),
                    "percentage": overlap_pct,
                    "only_semantic": list(set(semantic_ids) - set(tfidf_ids)),
                    "only_tfidf": list(set(tfidf_ids) - set(semantic_ids)),
                },
            }
    
    async def run_benchmark_suite(
        self,
        queries: List[str],
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Run benchmark suite with multiple queries.
        
        Args:
            queries: List of test queries
            top_k: Number of results
            
        Returns:
            Benchmark results with metrics
        """
        print("\n" + "="*70)
        print("TF-IDF BASELINE BENCHMARK")
        print("="*70)
        print(f"Number of queries: {len(queries)}")
        print(f"Results per query (top_k): {top_k}")
        print("="*70 + "\n")
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Benchmarking: '{query[:50]}...'")
            try:
                result = await self.run_comparison(query, top_k)
                self.results["benchmarks"].append(result)
                
                # Print summary for this query
                overlap_pct = result["overlap"]["percentage"]
                semantic_score = result["semantic"]["avg_score"]
                tfidf_score = result["tfidf"]["avg_score"]
                
                print(f"      Overlap: {overlap_pct:.1f}% | "
                      f"Semantic avg: {semantic_score:.4f} | "
                      f"TF-IDF avg: {tfidf_score:.4f}\n")
                
            except Exception as e:
                print(f"      ERROR: {e}\n")
        
        # Calculate summary statistics
        if self.results["benchmarks"]:
            overlaps = [b["overlap"]["percentage"] for b in self.results["benchmarks"]]
            semantic_scores = [b["semantic"]["avg_score"] for b in self.results["benchmarks"]]
            tfidf_scores = [b["tfidf"]["avg_score"] for b in self.results["benchmarks"]]
            
            self.results["summary"] = {
                "total_queries": len(self.results["benchmarks"]),
                "avg_overlap_percentage": sum(overlaps) / len(overlaps),
                "avg_semantic_score": sum(semantic_scores) / len(semantic_scores),
                "avg_tfidf_score": sum(tfidf_scores) / len(tfidf_scores),
                "min_overlap": min(overlaps),
                "max_overlap": max(overlaps),
            }
            
            # Print summary
            print("="*70)
            print("BENCHMARK SUMMARY")
            print("="*70)
            print(f"Total Queries: {self.results['summary']['total_queries']}")
            print(f"Avg Overlap: {self.results['summary']['avg_overlap_percentage']:.1f}%")
            print(f"Avg Semantic Score: {self.results['summary']['avg_semantic_score']:.4f}")
            print(f"Avg TF-IDF Score: {self.results['summary']['avg_tfidf_score']:.4f}")
            print(f"Min Overlap: {self.results['summary']['min_overlap']:.1f}%")
            print(f"Max Overlap: {self.results['summary']['max_overlap']:.1f}%")
            print("="*70 + "\n")
        
        return self.results
    
    def save_results(self, filepath: str = None) -> str:
        """
        Save benchmark results to JSON file.
        
        Args:
            filepath: Output file path (optional)
            
        Returns:
            Path to saved file
        """
        if not filepath:
            filename = f"baseline_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(
                os.path.dirname(__file__),
                "benchmark_results",
                filename
            )
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to: {filepath}")
        return filepath


async def main():
    """Run benchmark with sample queries."""
    
    # Sample test queries (customize based on your domain)
    test_queries = [
        "machine learning in software testing",
        "code review automation",
        "CI/CD pipeline optimization",
        "software security vulnerability detection",
        "program analysis techniques",
        "requirements engineering methods",
        "software architecture patterns",
        "software maintenance strategies",
        "deep learning for code analysis",
        "software evolution and refactoring",
    ]
    
    benchmark = BaselineBenchmark()
    results = await benchmark.run_benchmark_suite(test_queries, top_k=10)
    
    # Save results
    benchmark.save_results()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
