"""
test_baseline.py - Test TF-IDF Baseline Integration

Quick test to verify baseline service is working correctly.
"""

import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import engine
from src.services.baseline_service import BaselineService
from src.services.search_service import SearchService
from src.schemas.search import SearchRequest
from src.core.enums import SearchMethod


async def test_baseline():
    """Test baseline service functionality."""
    
    print("\n" + "="*70)
    print("BASELINE SERVICE TEST")
    print("="*70 + "\n")
    
    async with AsyncSession(engine) as session:
        # Test 1: Initialize baseline
        print("1. Testing baseline initialization...")
        baseline = BaselineService(session)
        
        print("   Initializing TF-IDF model...")
        await baseline.initialize()
        
        if baseline.is_fitted():
            print("   ✓ Baseline initialized successfully")
        else:
            print("   ✗ Baseline initialization failed")
            return False
        
        # Test 2: Perform TF-IDF search
        print("\n2. Testing TF-IDF search...")
        test_query = "machine learning software testing"
        
        results = await baseline.search(test_query, top_k=5)
        
        if results.results:
            print(f"   ✓ Found {len(results.results)} results for query: '{test_query}'")
            print(f"   Method: {results.method}")
            print(f"   Top result: {results.results[0]['paper']['title'][:60]}...")
        else:
            print(f"   ✗ No results found")
            return False
        
        # Test 3: SearchService integration
        print("\n3. Testing SearchService integration...")
        search_service = SearchService(session)
        
        # Test keyword search through SearchService
        request = SearchRequest(
            query=test_query,
            method=SearchMethod.KEYWORD,
            top_k=5,
        )
        
        results = await search_service.search(request)
        
        if results.results:
            print(f"   ✓ SearchService keyword search working")
            print(f"   Found {len(results.results)} results")
        else:
            print(f"   ✗ SearchService search failed")
            return False
        
        # Test 4: Semantic vs TF-IDF comparison
        print("\n4. Testing semantic vs TF-IDF comparison...")
        
        # Get semantic results
        semantic_request = SearchRequest(
            query=test_query,
            method=SearchMethod.SEMANTIC,
            top_k=5,
        )
        semantic_results = await search_service.search(semantic_request)
        
        # Compare
        comparison = await baseline.compare_methods(
            query=test_query,
            semantic_results=semantic_results.results,
            top_k=5,
        )
        
        overlap = comparison["comparison"]["overlap_at_k"]
        overlap_pct = comparison["comparison"]["overlap_percentage"]
        
        print(f"   ✓ Comparison completed")
        print(f"   Semantic results: {len(semantic_results.results)}")
        print(f"   TF-IDF results: {len(comparison['tfidf']['paper_ids'])}")
        print(f"   Overlap: {overlap}/{5} ({overlap_pct:.1f}%)")
        print(f"   Only in semantic: {len(comparison['comparison']['only_in_semantic'])}")
        print(f"   Only in TF-IDF: {len(comparison['comparison']['only_in_tfidf'])}")
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70 + "\n")
        
        return True


async def main():
    try:
        success = await test_baseline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
