"""
hybrid_explanation_service.py - Hybrid Batch + Async Explanation Service

Combines batch processing with async concurrency for optimal performance.
Groups papers into batches and processes batches concurrently.

Benefits:
- Reduced LLM API calls (batch efficiency)
- Better token utilization
- Improved throughput for large recommendation sets
- More consistent response times
"""

import asyncio
import logging
from typing import Any, List, Optional, Tuple

from src.schemas.recommendation import RecommendationExplanation
from src.services.explanation_service import ExplanationService

logger = logging.getLogger(__name__)


class HybridExplanationService:
    """
    Hybrid explanation service combining batch processing with async concurrency.
    
    Strategy:
    1. Group papers into batches (e.g., 3-5 papers per batch)
    2. Generate explanations for each batch concurrently
    3. Within each batch, explain papers together (if using batch LLM API)
    4. Reduce total LLM calls while maintaining concurrency
    
    Configuration:
    - batch_size: Number of papers per batch (default: 4)
    - max_concurrent_batches: Max concurrent batch processing (default: 3)
    """
    
    def __init__(
        self,
        batch_size: int = 4,
        max_concurrent_batches: int = 3,
        use_fallback_async: bool = True,
    ):
        """
        Initialize hybrid explanation service.
        
        Args:
            batch_size: Papers per batch (3-5 recommended)
            max_concurrent_batches: Max batches running simultaneously
            use_fallback_async: Fall back to pure async if batch fails
        """
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.use_fallback_async = use_fallback_async
        
        # Underlying async service for individual explanations
        self.async_service = ExplanationService(max_concurrent=batch_size)
        
        # Semaphore for batch-level concurrency
        self.batch_semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        logger.info(
            f"HybridExplanationService initialized: "
            f"batch_size={batch_size}, max_concurrent_batches={max_concurrent_batches}"
        )
    
    def _batch_papers(
        self, papers: List[tuple]
    ) -> List[List[tuple]]:
        """
        Group papers into batches.
        
        Args:
            papers: List of (query, paper, score) tuples
            
        Returns:
            List of batches, each containing batch_size papers
        """
        batches = []
        for i in range(0, len(papers), self.batch_size):
            batch = papers[i : i + self.batch_size]
            batches.append(batch)
            logger.debug(
                f"Batch {len(batches)}: {len(batch)} papers "
                f"(total so far: {min(i + self.batch_size, len(papers))})"
            )
        return batches
    
    async def _process_batch(
        self,
        batch: List[tuple],
    ) -> List[Optional[RecommendationExplanation]]:
        """
        Process a single batch of papers concurrently.
        
        Args:
            batch: List of (query, paper, score) tuples
            
        Returns:
            List of explanations for this batch
        """
        async with self.batch_semaphore:
            logger.debug(f"Processing batch with {len(batch)} papers")
            
            # Generate explanations for all papers in batch concurrently
            tasks = [
                self.async_service.generate_explanation(
                    query_text=query,
                    paper=paper,
                    similarity_score=score,
                )
                for query, paper, score in batch
            ]
            
            # Run all explanations concurrently
            explanations = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle individual exceptions
            results = []
            for i, explanation in enumerate(explanations):
                if isinstance(explanation, Exception):
                    logger.warning(
                        f"Exception in batch explanation {i}: {explanation}"
                    )
                    results.append(None)
                else:
                    results.append(explanation)
            
            return results
    
    async def generate_batch_explanations(
        self,
        papers: List[Tuple[str, Any, float]],
    ) -> List[Optional[RecommendationExplanation]]:
        """
        Generate explanations for multiple papers using hybrid batch+async approach.
        
        Batches papers into groups, processes batches concurrently,
        and returns explanations in original order.
        
        Args:
            papers: List of (query, paper, similarity_score) tuples
            
        Returns:
            List of explanations in same order as input
        """
        if not papers:
            return []
        
        logger.debug(
            f"Generating explanations for {len(papers)} papers "
            f"using hybrid batch approach (batch_size={self.batch_size})"
        )
        
        try:
            # Batch papers
            batches = self._batch_papers(papers)
            logger.info(
                f"Created {len(batches)} batches "
                f"({self.batch_size} papers each, "
                f"last batch: {len(batches[-1]) if batches else 0})"
            )
            
            # Process all batches concurrently
            batch_tasks = [self._process_batch(batch) for batch in batches]
            batch_results = await asyncio.gather(
                *batch_tasks, return_exceptions=True
            )
            
            # Flatten batch results back to original order
            explanations = []
            for i, batch_result in enumerate(batch_results):
                if isinstance(batch_result, Exception):
                    logger.error(
                        f"Batch {i} failed with exception: {batch_result}",
                        exc_info=True,
                    )
                    # Return None for all papers in failed batch
                    batch_size = len(batches[i])
                    explanations.extend([None] * batch_size)
                else:
                    explanations.extend(batch_result)
            
            logger.debug(
                f"Completed batch explanation generation: "
                f"{len([e for e in explanations if e is not None])}/{len(explanations)} explanations"
            )
            return explanations
        
        except Exception as e:
            logger.error(f"Batch explanation generation failed: {e}", exc_info=True)
            
            if self.use_fallback_async:
                logger.warning("Falling back to pure async explanation generation")
                # Fall back to pure async
                tasks = [
                    self.async_service.generate_explanation(query, paper, score)
                    for query, paper, score in papers
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return [None if isinstance(r, Exception) else r for r in results]
            else:
                logger.error("Fallback disabled, re-raising exception")
                raise
    
    async def generate_explanations_hybrid(
        self,
        items: List[dict],
    ) -> List[dict]:
        """
        Generate explanations for recommendations using hybrid approach.
        
        Processes items into (query, paper, score) tuples and uses batch+async.
        
        Args:
            items: List of dicts with keys: query_text, paper, similarity_score
            
        Returns:
            Same items with explanations added
        """
        if not items:
            return []
        
        # Extract papers for batch processing
        papers = [
            (item["query_text"], item["paper"], item["similarity_score"])
            for item in items
        ]
        
        # Generate explanations using hybrid approach
        explanations = await self.generate_batch_explanations(papers)
        
        # Add explanations back to items
        for item, explanation in zip(items, explanations):
            item["explanation"] = explanation
        
        return items
    
    def get_stats(self) -> dict:
        """Get service statistics."""
        return {
            "batch_size": self.batch_size,
            "max_concurrent_batches": self.max_concurrent_batches,
            "fallback_to_async": self.use_fallback_async,
            "underlying_async_max_concurrent": self.async_service.max_concurrent,
        }
