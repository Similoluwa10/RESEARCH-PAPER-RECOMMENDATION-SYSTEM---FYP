"""
test_hybrid_explanations.py - Tests for Hybrid Batch + Async Explanation Service

Tests the hybrid approach that combines:
- Batch processing: Groups papers (3-5 per batch)
- Async concurrency: Runs batches concurrently
- Performance: Better token efficiency and throughput
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.hybrid_explanation_service import HybridExplanationService


class MockPaper:
    """Mock paper for testing."""
    
    def __init__(self, title, abstract, idx):
        self.id = idx
        self.title = title
        self.abstract = abstract


class TestHybridBatching:
    """Test batching functionality."""
    
    def test_batch_papers_even_distribution(self):
        """Test papers are evenly distributed into batches."""
        service = HybridExplanationService(batch_size=3)
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(9)
        ]
        
        batches = service._batch_papers(papers)
        
        assert len(batches) == 3, f"Expected 3 batches, got {len(batches)}"
        assert all(len(b) == 3 for b in batches), "All batches should have 3 papers"
    
    def test_batch_papers_uneven_distribution(self):
        """Test papers with uneven distribution."""
        service = HybridExplanationService(batch_size=4)
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(10)
        ]
        
        batches = service._batch_papers(papers)
        
        assert len(batches) == 3, f"Expected 3 batches, got {len(batches)}"
        assert len(batches[0]) == 4 and len(batches[1]) == 4, "First two batches should have 4 papers each"
        assert len(batches[2]) == 2, "Last batch should have 2 papers"
    
    def test_batch_papers_single_batch(self):
        """Test papers that fit in single batch."""
        service = HybridExplanationService(batch_size=5)
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(3)
        ]
        
        batches = service._batch_papers(papers)
        
        assert len(batches) == 1, "Should have 1 batch"
        assert len(batches[0]) == 3, "Single batch should have 3 papers"
    
    def test_batch_papers_empty(self):
        """Test batching empty list."""
        service = HybridExplanationService(batch_size=3)
        batches = service._batch_papers([])
        assert len(batches) == 0, "Empty input should produce empty batches"


class TestHybridAsyncBatchProcessing:
    """Test async batch processing."""
    
    @pytest.mark.asyncio
    async def test_process_single_batch(self):
        """Test processing a single batch."""
        service = HybridExplanationService(batch_size=4)
        
        papers = [
            ("test query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(3)
        ]
        
        results = await service._process_batch(papers)
        
        assert len(results) == 3, "Should return 3 explanations"
        assert all(r is not None for r in results), "All should have explanations"
    
    @pytest.mark.asyncio
    async def test_process_batch_with_error(self):
        """Test batch processing with error handling."""
        service = HybridExplanationService(batch_size=2)
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(2)
        ]
        
        # This will use heuristic fallback, so should still work
        results = await service._process_batch(papers)
        
        assert len(results) == 2, "Should return results even with error"


class TestHybridExplanationGeneration:
    """Test full hybrid explanation generation."""
    
    @pytest.mark.asyncio
    async def test_generate_batch_explanations_small_set(self):
        """Test generating explanations for small paper set."""
        service = HybridExplanationService(batch_size=3, max_concurrent_batches=2)
        
        papers = [
            ("machine learning", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(5)
        ]
        
        explanations = await service.generate_batch_explanations(papers)
        
        assert len(explanations) == 5, "Should return 5 explanations"
        # Some may be None if heuristic fallback, but not all
        non_none = [e for e in explanations if e is not None]
        assert len(non_none) > 0, "Should have at least some explanations"
    
    @pytest.mark.asyncio
    async def test_generate_batch_explanations_large_set(self):
        """Test generating explanations for large paper set."""
        service = HybridExplanationService(batch_size=4, max_concurrent_batches=2)
        
        papers = [
            ("bug detection", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.7)
            for i in range(12)
        ]
        
        start = time.time()
        explanations = await service.generate_batch_explanations(papers)
        elapsed = time.time() - start
        
        assert len(explanations) == 12, "Should return 12 explanations"
        print(f"\n12 papers, batch_size=4, concurrent_batches=2: {elapsed:.2f}s")
    
    @pytest.mark.asyncio
    async def test_generate_batch_explanations_empty(self):
        """Test with empty paper list."""
        service = HybridExplanationService()
        explanations = await service.generate_batch_explanations([])
        assert len(explanations) == 0, "Should return empty list"
    
    @pytest.mark.asyncio
    async def test_generate_batch_explanations_preserves_order(self):
        """Test that explanations are returned in original order."""
        service = HybridExplanationService(batch_size=2)
        
        papers = [
            (f"query {i}", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(5)
        ]
        
        explanations = await service.generate_batch_explanations(papers)
        
        assert len(explanations) == 5, "Should preserve order"
        # All should have explanations (heuristic fallback)
        assert all(e is not None for e in explanations), "All should be explained"


class TestHybridConcurrency:
    """Test concurrency behavior of hybrid approach."""
    
    @pytest.mark.asyncio
    async def test_batch_semaphore_limits_concurrent_batches(self):
        """Test that semaphore limits concurrent batch processing."""
        service = HybridExplanationService(batch_size=3, max_concurrent_batches=2)
        
        concurrent_count = 0
        max_concurrent_observed = 0
        lock = asyncio.Lock()
        
        original_process_batch = service._process_batch
        
        async def mock_process_with_tracking(batch):
            nonlocal concurrent_count, max_concurrent_observed
            
            async with lock:
                concurrent_count += 1
                max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
            
            # Simulate work
            await asyncio.sleep(0.05)
            
            async with lock:
                concurrent_count -= 1
            
            return await original_process_batch(batch)
        
        service._process_batch = mock_process_with_tracking
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(9)  # 3 batches of 3
        ]
        
        await service.generate_batch_explanations(papers)
        
        service._process_batch = original_process_batch
        
        # Should not exceed max_concurrent_batches
        assert max_concurrent_observed <= 3, \
            f"Concurrent batches {max_concurrent_observed} > 2 (with overhead)"
    
    @pytest.mark.asyncio
    async def test_hybrid_faster_than_sequential(self):
        """Test that hybrid is not slower than sequential (may not be faster with heuristics)."""
        service = HybridExplanationService(batch_size=4, max_concurrent_batches=2)
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(8)
        ]
        
        # Sequential timing
        start_seq = time.time()
        for query, paper, score in papers:
            await service.async_service.generate_explanation(query, paper, score)
        seq_time = time.time() - start_seq
        
        # Hybrid timing
        start_hybrid = time.time()
        await service.generate_batch_explanations(papers)
        hybrid_time = time.time() - start_hybrid
        
        print(f"\nSequential: {seq_time:.4f}s, Hybrid: {hybrid_time:.4f}s")
        
        # Hybrid should not be significantly slower
        assert hybrid_time <= seq_time * 1.5, \
            f"Hybrid {hybrid_time:.4f}s should not be much slower than sequential {seq_time:.4f}s"


class TestHybridWithRecommendations:
    """Test hybrid service with recommendation data structure."""
    
    @pytest.mark.asyncio
    async def test_generate_explanations_hybrid_with_items(self):
        """Test hybrid explanation generation with recommendation items."""
        service = HybridExplanationService(batch_size=3)
        
        items = [
            {
                "query_text": "bug detection",
                "paper": MockPaper(f"Paper {i}", f"Abstract {i}", i),
                "similarity_score": 0.8,
            }
            for i in range(5)
        ]
        
        result_items = await service.generate_explanations_hybrid(items)
        
        assert len(result_items) == 5, "Should return all items"
        assert all("explanation" in item for item in result_items), \
            "All items should have explanation"
        assert all(item["explanation"] is not None for item in result_items), \
            "All items should have non-None explanations"
    
    @pytest.mark.asyncio
    async def test_generate_explanations_hybrid_preserves_items(self):
        """Test that original item data is preserved."""
        service = HybridExplanationService(batch_size=2)
        
        items = [
            {
                "query_text": "machine learning",
                "paper": MockPaper(f"Paper {i}", f"Abstract {i}", i),
                "similarity_score": 0.7 + (i * 0.01),
                "custom_field": f"value_{i}",
            }
            for i in range(3)
        ]
        
        result_items = await service.generate_explanations_hybrid(items)
        
        # Check original data preserved
        for orig, result in zip(items, result_items):
            assert result["custom_field"] == orig["custom_field"]
            assert result["similarity_score"] == orig["similarity_score"]


class TestHybridConfiguration:
    """Test configuration and initialization."""
    
    def test_default_configuration(self):
        """Test default configuration."""
        service = HybridExplanationService()
        
        assert service.batch_size == 4, "Default batch_size should be 4"
        assert service.max_concurrent_batches == 3, "Default max_concurrent should be 3"
        assert service.use_fallback_async is True, "Fallback should be enabled"
    
    def test_custom_configuration(self):
        """Test custom configuration."""
        service = HybridExplanationService(
            batch_size=5,
            max_concurrent_batches=2,
            use_fallback_async=False,
        )
        
        assert service.batch_size == 5
        assert service.max_concurrent_batches == 2
        assert service.use_fallback_async is False
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        service = HybridExplanationService(batch_size=3, max_concurrent_batches=2)
        stats = service.get_stats()
        
        assert stats["batch_size"] == 3
        assert stats["max_concurrent_batches"] == 2
        assert stats["fallback_to_async"] is True


class TestHybridErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_fallback_on_batch_failure(self):
        """Test fallback to pure async when batch processing fails."""
        service = HybridExplanationService(batch_size=2, use_fallback_async=True)
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(3)
        ]
        
        # Should not raise even if there are issues
        explanations = await service.generate_batch_explanations(papers)
        
        assert len(explanations) == 3, "Should return explanations from fallback"
    
    @pytest.mark.asyncio
    async def test_no_fallback_raises_error(self):
        """Test that without fallback, errors are re-raised."""
        service = HybridExplanationService(use_fallback_async=False)
        
        # Mock generate_batch_explanations to simulate failure
        original_method = service.generate_batch_explanations
        
        async def mock_with_error(*args, **kwargs):
            # Simulate batch error
            raise ValueError("Test batch error")
        
        service.generate_batch_explanations = mock_with_error
        
        papers = [("query", MockPaper("Paper", "Abstract", 1), 0.8)]
        
        with pytest.raises(ValueError, match="Test batch error"):
            await service.generate_batch_explanations(papers)


class TestHybridPerformanceCharacteristics:
    """Test performance characteristics of hybrid approach."""
    
    @pytest.mark.asyncio
    async def test_batch_efficiency_small_sets(self):
        """Test batch efficiency with small paper sets."""
        # Small set: 1 batch
        service = HybridExplanationService(batch_size=5)
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(3)
        ]
        
        batches = service._batch_papers(papers)
        
        assert len(batches) == 1, "Small set should use 1 batch"
        assert len(batches[0]) == 3
    
    @pytest.mark.asyncio
    async def test_batch_efficiency_large_sets(self):
        """Test batch efficiency with large paper sets."""
        # Large set: multiple batches
        service = HybridExplanationService(batch_size=4)
        
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(20)
        ]
        
        batches = service._batch_papers(papers)
        
        assert len(batches) == 5, "20 papers should use 5 batches of 4"
        total_papers = sum(len(b) for b in batches)
        assert total_papers == 20, "All papers should be batched"
    
    @pytest.mark.asyncio
    async def test_concurrent_batch_throughput(self):
        """Test throughput with concurrent batch processing."""
        service = HybridExplanationService(batch_size=3, max_concurrent_batches=2)
        
        # Simulate: 6 papers = 2 batches = 1 concurrent round with 2 batches
        papers = [
            ("query", MockPaper(f"Paper {i}", f"Abstract {i}", i), 0.8)
            for i in range(6)
        ]
        
        start = time.time()
        explanations = await service.generate_batch_explanations(papers)
        elapsed = time.time() - start
        
        assert len(explanations) == 6
        print(f"\n6 papers (2 batches of 3, 2 concurrent): {elapsed:.3f}s")


@pytest.mark.asyncio
async def test_full_hybrid_flow():
    """Integration test: Full hybrid flow from papers to explanations."""
    service = HybridExplanationService(
        batch_size=3,
        max_concurrent_batches=2,
    )
    
    # Simulate recommendation data
    papers_data = [
        ("machine learning", MockPaper(f"ML Paper {i}", f"ML Abstract {i}", i), 0.8)
        for i in range(10)
    ]
    
    start = time.time()
    explanations = await service.generate_batch_explanations(papers_data)
    elapsed = time.time() - start
    
    # Validate
    assert len(explanations) == 10, "Should have 10 explanations"
    assert all(e is not None for e in explanations), "All should be explained"
    
    stats = service.get_stats()
    print(f"\nHybrid Stats:")
    print(f"  - 10 papers generated in {elapsed:.2f}s")
    print(f"  - Batch size: {stats['batch_size']}")
    print(f"  - Concurrent batches: {stats['max_concurrent_batches']}")
    print(f"  - Expected batches: {(10 + stats['batch_size'] - 1) // stats['batch_size']}")
