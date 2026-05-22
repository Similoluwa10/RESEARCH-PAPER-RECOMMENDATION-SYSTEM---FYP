"""
Test TF-IDF Baseline Implementation

Comprehensive testing of TF-IDF baseline performance against semantic search.
Tests search functionality, comparison metrics, and evaluation.
"""

import asyncio
import sys
import os
from typing import List, Tuple
import json
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages'))

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import engine
from src.repositories.paper_repository import PaperRepository
from src.services.search_service import SearchService
from src.services.baseline_service import BaselineService
from src.schemas.search import SearchRequest, SearchFilters
from src.core.enums import SearchMethod
from nlp.src.baselines import TFIDFBaseline


class BaselineTestSuite:
    """Test suite for TF-IDF baseline."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {},
        }
    
    async def test_tfidf_initialization(self, db: AsyncSession) -> bool:
        """Test TF-IDF model initialization."""
        print("\n" + "="*70)
        print("TEST 1: TF-IDF Initialization")
        print("="*70)
        
        try:
            baseline_service = BaselineService(db)
            await baseline_service.initialize()
            
            if baseline_service._is_fitted:
                print("✓ TF-IDF model initialized successfully")
                print(f"  - Papers loaded: {len(baseline_service._corpus_papers)}")
                print(f"  - Model is fitted: {baseline_service._is_fitted}")
                self.results["tests"].append({
                    "name": "TF-IDF Initialization",
                    "status": "PASSED",
                    "papers_count": len(baseline_service._corpus_papers),
                })
                return True
            else:
                print("✗ TF-IDF model initialization failed")
                self.results["tests"].append({
                    "name": "TF-IDF Initialization",
                    "status": "FAILED",
                    "error": "Model not fitted",
                })
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results["tests"].append({
                "name": "TF-IDF Initialization",
                "status": "FAILED",
                "error": str(e),
            })
            return False
    
    async def test_tfidf_search(self, db: AsyncSession) -> bool:
        """Test TF-IDF search functionality."""
        print("\n" + "="*70)
        print("TEST 2: TF-IDF Search Functionality")
        print("="*70)
        
        try:
            baseline_service = BaselineService(db)
            await baseline_service.initialize()
            
            test_queries = [
                "machine learning algorithms",
                "software testing techniques",
                "security vulnerabilities",
                "code review practices",
            ]
            
            all_passed = True
            search_results = []
            
            for query in test_queries:
                response = await baseline_service.search(query, top_k=5)
                search_results.append({
                    "query": query,
                    "results_count": response.total,
                    "top_result": response.results[0].paper.title if response.results else None,
                    "scores": [r.score for r in response.results[:3]],
                })
                
                if response.total > 0:
                    print(f"✓ Query: '{query}'")
                    print(f"  - Results found: {response.total}")
                    print(f"  - Top result: {response.results[0].paper.title[:60]}...")
                    print(f"  - Scores: {[f'{s:.4f}' for s in search_results[-1]['scores']]}")
                else:
                    print(f"✗ Query: '{query}' - No results found")
                    all_passed = False
            
            self.results["tests"].append({
                "name": "TF-IDF Search",
                "status": "PASSED" if all_passed else "FAILED",
                "sample_searches": search_results,
            })
            
            return all_passed
            
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results["tests"].append({
                "name": "TF-IDF Search",
                "status": "FAILED",
                "error": str(e),
            })
            return False
    
    async def test_semantic_vs_tfidf(self, db: AsyncSession) -> bool:
        """Compare semantic vs TF-IDF search results."""
        print("\n" + "="*70)
        print("TEST 3: Semantic vs TF-IDF Comparison")
        print("="*70)
        
        try:
            service = SearchService(db)
            
            test_queries = [
                "neural networks and deep learning",
                "agile software development",
                "cloud computing infrastructure",
            ]
            
            comparisons = []
            
            for query in test_queries:
                print(f"\nQuery: '{query}'")
                
                # Semantic search
                semantic_request = SearchRequest(
                    query=query,
                    method=SearchMethod.SEMANTIC,
                    top_k=5,
                    filters=SearchFilters(),
                )
                semantic_response = await service.search(semantic_request)
                
                # TF-IDF search
                tfidf_request = SearchRequest(
                    query=query,
                    method=SearchMethod.KEYWORD,
                    top_k=5,
                    filters=SearchFilters(),
                )
                tfidf_response = await service.search(tfidf_request)
                
                # Extract IDs for comparison
                semantic_ids = set(r.paper.id for r in semantic_response.results)
                tfidf_ids = set(r.paper.id for r in tfidf_response.results)
                
                overlap = semantic_ids & tfidf_ids
                
                comparison = {
                    "query": query,
                    "semantic_results": semantic_response.total,
                    "tfidf_results": tfidf_response.total,
                    "overlap": len(overlap),
                    "overlap_percentage": (len(overlap) / max(len(semantic_ids), len(tfidf_ids)) * 100) if max(len(semantic_ids), len(tfidf_ids)) > 0 else 0,
                    "semantic_top": semantic_response.results[0].paper.title if semantic_response.results else None,
                    "tfidf_top": tfidf_response.results[0].paper.title if tfidf_response.results else None,
                }
                
                comparisons.append(comparison)
                
                print(f"  Semantic results: {semantic_response.total}")
                print(f"  TF-IDF results: {tfidf_response.total}")
                print(f"  Overlap: {len(overlap)}/{min(len(semantic_ids), len(tfidf_ids))} ({comparison['overlap_percentage']:.1f}%)")
                print(f"  Semantic top: {comparison['semantic_top'][:50]}..." if comparison['semantic_top'] else "  Semantic top: None")
                print(f"  TF-IDF top: {comparison['tfidf_top'][:50]}..." if comparison['tfidf_top'] else "  TF-IDF top: None")
            
            self.results["tests"].append({
                "name": "Semantic vs TF-IDF",
                "status": "PASSED",
                "comparisons": comparisons,
            })
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results["tests"].append({
                "name": "Semantic vs TF-IDF",
                "status": "FAILED",
                "error": str(e),
            })
            return False
    
    async def test_tfidf_with_filters(self, db: AsyncSession) -> bool:
        """Test TF-IDF search with category and year filters."""
        print("\n" + "="*70)
        print("TEST 4: TF-IDF with Filters")
        print("="*70)
        
        try:
            baseline_service = BaselineService(db)
            await baseline_service.initialize()
            
            # Test with category filter
            print("\nTesting with category filter...")
            response = await baseline_service.search(
                query="machine learning",
                top_k=5,
                filters={"category": "Machine Learning for SE"}
            )
            
            if response.total > 0 and all(r.paper.category == "Machine Learning for SE" for r in response.results):
                print(f"✓ Category filter working - {response.total} results")
                for i, result in enumerate(response.results[:3], 1):
                    print(f"  {i}. {result.paper.title[:60]}...")
                
                self.results["tests"].append({
                    "name": "TF-IDF with Filters",
                    "status": "PASSED",
                    "filtered_results": response.total,
                })
                return True
            else:
                print(f"✗ Filter test failed")
                self.results["tests"].append({
                    "name": "TF-IDF with Filters",
                    "status": "FAILED",
                    "error": "Filter not applied correctly",
                })
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results["tests"].append({
                "name": "TF-IDF with Filters",
                "status": "FAILED",
                "error": str(e),
            })
            return False
    
    async def test_search_performance(self, db: AsyncSession) -> bool:
        """Test search performance and timing."""
        print("\n" + "="*70)
        print("TEST 5: Search Performance")
        print("="*70)
        
        try:
            import time
            service = SearchService(db)
            
            test_queries = [
                "software testing",
                "machine learning",
                "security",
            ]
            
            performance_metrics = []
            
            for query in test_queries:
                # Test semantic search timing
                start = time.time()
                semantic_request = SearchRequest(
                    query=query,
                    method=SearchMethod.SEMANTIC,
                    top_k=10,
                    filters=SearchFilters(),
                )
                semantic_response = await service.search(semantic_request)
                semantic_time = time.time() - start
                
                # Test TF-IDF search timing
                start = time.time()
                tfidf_request = SearchRequest(
                    query=query,
                    method=SearchMethod.KEYWORD,
                    top_k=10,
                    filters=SearchFilters(),
                )
                tfidf_response = await service.search(tfidf_request)
                tfidf_time = time.time() - start
                
                metric = {
                    "query": query,
                    "semantic_time_ms": semantic_time * 1000,
                    "tfidf_time_ms": tfidf_time * 1000,
                    "speedup": semantic_time / tfidf_time if tfidf_time > 0 else 0,
                }
                performance_metrics.append(metric)
                
                print(f"\nQuery: '{query}'")
                print(f"  Semantic: {semantic_time*1000:.2f}ms")
                print(f"  TF-IDF:   {tfidf_time*1000:.2f}ms")
                print(f"  TF-IDF is {metric['speedup']:.2f}x {'faster' if metric['speedup'] > 1 else 'slower'}")
            
            self.results["tests"].append({
                "name": "Search Performance",
                "status": "PASSED",
                "metrics": performance_metrics,
            })
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results["tests"].append({
                "name": "Search Performance",
                "status": "FAILED",
                "error": str(e),
            })
            return False
    
    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "="*70)
        print("TF-IDF BASELINE TEST SUITE")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        async with AsyncSession(engine) as db:
            results = [
                await self.test_tfidf_initialization(db),
                await self.test_tfidf_search(db),
                await self.test_semantic_vs_tfidf(db),
                await self.test_tfidf_with_filters(db),
                await self.test_search_performance(db),
            ]
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Passed: {passed}/{total}")
        print(f"Status: {'✓ ALL TESTS PASSED' if passed == total else '✗ SOME TESTS FAILED'}")
        
        self.results["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
        }
        
        # Save results
        report_file = os.path.join(
            os.path.dirname(__file__), 
            'baseline_test_report.json'
        )
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nTest report saved to: {report_file}")
        print("="*70)


async def main():
    """Run the test suite."""
    suite = BaselineTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
