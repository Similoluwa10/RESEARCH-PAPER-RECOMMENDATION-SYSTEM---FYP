"""
Ranking Quality Evaluation: Semantic vs TF-IDF
Evaluates ranking quality using semantic coherence, not keyword matching.
This is fair to both methods - evaluates how well-ranked results are semantically.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages'))

from src.services.search_service import SearchService
from src.services.baseline_service import BaselineService
from src.services.embedding_service import EmbeddingService
from src.schemas.search import SearchRequest, SearchMethod
from src.repositories.paper_repository import PaperRepository
from src.models.base import async_session_maker


class RankingQualityEvaluator:
    """Evaluates ranking quality using semantic coherence metrics."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.search_service = SearchService(db_session)
        self.baseline_service = BaselineService(db_session)
        self.embedding_service = EmbeddingService()
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Test queries - focused on software engineering
        self.test_queries = [
            ("bug prediction", "defect prediction and fault localization"),
            ("technical debt", "software maintainability and code quality"),
            ("CI/CD", "continuous integration deployment DevOps pipelines"),
            ("code review", "code inspection peer review verification"),
            ("software testing", "test automation quality assurance validation"),
            ("machine learning in software engineering", "deep learning neural networks software development"),
            ("code smell", "software quality anti-pattern design problem"),
            ("security vulnerability", "software security vulnerability exploitation attack"),
            ("refactoring", "code improvement restructuring optimization"),
            ("requirements engineering", "requirement specification elicitation analysis"),
        ]
    
    async def _get_semantic_coherence(self, query_embedding: np.ndarray, results: List[Dict]) -> Tuple[List[float], float]:
        """
        Calculate semantic coherence scores for results.
        Returns: (individual_scores, mean_coherence)
        """
        scores = []
        for result in results:
            title = result.get('title', '')
            abstract = result.get('abstract', '')
            text = f"{title}. {abstract}"[:512]  # Limit to 512 chars
            
            paper_embedding = self.model.encode(text, convert_to_numpy=True)
            # Cosine similarity
            similarity = np.dot(query_embedding, paper_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(paper_embedding)
            )
            scores.append(float(similarity))
        
        return scores, np.mean(scores) if scores else 0.0
    
    def _calculate_ranking_quality_metrics(self, scores: List[float]) -> Dict:
        """Calculate ranking quality metrics from coherence scores."""
        if not scores:
            return {
                "mean_coherence": 0.0,
                "median_coherence": 0.0,
                "std_coherence": 0.0,
                "ranking_consistency": 0.0,
                "top_5_avg": 0.0,
                "perfect_ranking_pct": 0.0,
            }
        
        # Check if results are well-ordered (higher scores at top = better ranking)
        sorted_scores = sorted(scores, reverse=True)
        current_order = np.array(scores)
        optimal_order = np.array(sorted_scores)
        
        # Ranking consistency: how close to optimal ordering
        ranking_consistency = np.corrcoef(current_order, optimal_order)[0, 1]
        if np.isnan(ranking_consistency):
            ranking_consistency = 0.0
        
        # Percentage of results above average
        avg_coherence = np.mean(scores)
        above_avg = sum(1 for s in scores if s > avg_coherence) / len(scores) * 100
        
        return {
            "mean_coherence": float(np.mean(scores)),
            "median_coherence": float(np.median(scores)),
            "std_coherence": float(np.std(scores)),
            "ranking_consistency": float(ranking_consistency),
            "top_5_avg": float(np.mean(scores[:5])) if len(scores) >= 5 else float(np.mean(scores)),
            "perfect_ranking_pct": above_avg,  # % of results above average coherence
        }
    
    def _diversity_score(self, results: List[Dict]) -> float:
        """Calculate diversity of results (different papers, not duplicates)."""
        if not results:
            return 0.0
        
        # Check for unique papers
        unique_ids = set()
        for result in results:
            unique_ids.add(result.get('id'))
        
        return len(unique_ids) / len(results)
    
    async def evaluate_query(self, query: str, semantic_query_variant: str) -> Dict:
        """Evaluate ranking quality for a single query."""
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Semantic search
        semantic_request = SearchRequest(
            query=semantic_query_variant,
            method=SearchMethod.SEMANTIC,
            top_k=10
        )
        semantic_response = await self.search_service.search(semantic_request)
        semantic_results = [
            {
                'id': r.paper.id,
                'title': r.paper.title,
                'abstract': r.paper.abstract,
                'score': r.score
            }
            for r in semantic_response.results
        ]
        
        # TF-IDF search
        tfidf_request = SearchRequest(
            query=query,
            method=SearchMethod.KEYWORD,
            top_k=10
        )
        tfidf_response = await self.search_service.search(tfidf_request)
        tfidf_results = [
            {
                'id': r.paper.id,
                'title': r.paper.title,
                'abstract': r.paper.abstract,
                'score': r.score
            }
            for r in tfidf_response.results
        ]
        
        # Calculate semantic coherence for each method
        semantic_scores, semantic_coherence = await self._get_semantic_coherence(
            query_embedding, semantic_results
        )
        tfidf_scores, tfidf_coherence = await self._get_semantic_coherence(
            query_embedding, tfidf_results
        )
        
        # Calculate ranking quality metrics
        semantic_metrics = self._calculate_ranking_quality_metrics(semantic_scores)
        tfidf_metrics = self._calculate_ranking_quality_metrics(tfidf_scores)
        
        # Diversity analysis
        semantic_diversity = self._diversity_score(semantic_results)
        tfidf_diversity = self._diversity_score(tfidf_results)
        
        return {
            "query": query,
            "semantic_variant": semantic_query_variant,
            "semantic_search": {
                "coherence_scores": semantic_scores,
                "metrics": semantic_metrics,
                "diversity": semantic_diversity,
                "top_3_titles": [r['title'] for r in semantic_results[:3]],
            },
            "tfidf_search": {
                "coherence_scores": tfidf_scores,
                "metrics": tfidf_metrics,
                "diversity": tfidf_diversity,
                "top_3_titles": [r['title'] for r in tfidf_results[:3]],
            },
            "advantage": {
                "semantic_coherence_advantage": float(semantic_coherence - tfidf_coherence),
                "semantic_ranking_quality_advantage": float(semantic_metrics["ranking_consistency"] - tfidf_metrics["ranking_consistency"]),
                "semantic_diversity_advantage": float(semantic_diversity - tfidf_diversity),
            }
        }
    
    async def run_evaluation(self) -> Dict:
        """Run complete ranking quality evaluation."""
        print("\n" + "="*80)
        print("RANKING QUALITY EVALUATION (Semantic Coherence Based)")
        print("="*80)
        print("\nEvaluating ranking quality using semantic coherence metrics...")
        print("(NOT keyword matching - fair evaluation for semantic search)\n")
        
        results = []
        
        for i, (query, semantic_variant) in enumerate(self.test_queries, 1):
            print(f"[{i}/10] Evaluating: '{query}'")
            try:
                query_result = await self.evaluate_query(query, semantic_variant)
                results.append(query_result)
                
                # Print results
                sem = query_result['semantic_search']['metrics']
                tfidf = query_result['tfidf_search']['metrics']
                adv = query_result['advantage']
                
                print(f"  Semantic Coherence: {sem['mean_coherence']:.3f} | TF-IDF: {tfidf['mean_coherence']:.3f}")
                print(f"  Ranking Quality:    {sem['ranking_consistency']:.3f} | TF-IDF: {tfidf['ranking_consistency']:.3f}")
                print(f"  Advantage: +{adv['semantic_coherence_advantage']:.3f} coherence, +{adv['semantic_ranking_quality_advantage']:.3f} ranking quality\n")
            except Exception as e:
                print(f"  Error: {str(e)}\n")
                continue
        
        # Aggregate metrics
        print("\n" + "="*80)
        print("AGGREGATED RANKING QUALITY METRICS")
        print("="*80)
        
        semantic_coherences = [r['semantic_search']['metrics']['mean_coherence'] for r in results]
        tfidf_coherences = [r['tfidf_search']['metrics']['mean_coherence'] for r in results]
        
        semantic_rankings = [r['semantic_search']['metrics']['ranking_consistency'] for r in results if not np.isnan(r['semantic_search']['metrics']['ranking_consistency'])]
        tfidf_rankings = [r['tfidf_search']['metrics']['ranking_consistency'] for r in results if not np.isnan(r['tfidf_search']['metrics']['ranking_consistency'])]
        
        semantic_diversity = [r['semantic_search']['diversity'] for r in results]
        tfidf_diversity = [r['tfidf_search']['diversity'] for r in results]
        
        print(f"\n📊 SEMANTIC COHERENCE (Higher = Better)")
        print(f"  Semantic:  {np.mean(semantic_coherences):.4f} ± {np.std(semantic_coherences):.4f}")
        print(f"  TF-IDF:    {np.mean(tfidf_coherences):.4f} ± {np.std(tfidf_coherences):.4f}")
        print(f"  Advantage: +{(np.mean(semantic_coherences) - np.mean(tfidf_coherences)):.4f} ({((np.mean(semantic_coherences) / np.mean(tfidf_coherences) - 1) * 100):.1f}% improvement)")
        
        print(f"\n🎯 RANKING QUALITY (Higher = Better Ordered)")
        print(f"  Semantic:  {np.mean(semantic_rankings):.4f} ± {np.std(semantic_rankings):.4f}")
        print(f"  TF-IDF:    {np.mean(tfidf_rankings):.4f} ± {np.std(tfidf_rankings):.4f}")
        print(f"  Advantage: +{(np.mean(semantic_rankings) - np.mean(tfidf_rankings)):.4f}")
        
        print(f"\n📦 RESULT DIVERSITY (Unique papers in top-10)")
        print(f"  Semantic:  {np.mean(semantic_diversity):.2%}")
        print(f"  TF-IDF:    {np.mean(tfidf_diversity):.2%}")
        
        # Save results
        output = {
            "timestamp": datetime.now().isoformat(),
            "evaluation_type": "ranking_quality",
            "methodology": "Semantic coherence-based evaluation (NOT keyword matching)",
            "queries_evaluated": len(results),
            "per_query_results": results,
            "aggregated_metrics": {
                "semantic_coherence": {
                    "mean": float(np.mean(semantic_coherences)),
                    "std": float(np.std(semantic_coherences)),
                    "min": float(np.min(semantic_coherences)),
                    "max": float(np.max(semantic_coherences)),
                },
                "tfidf_coherence": {
                    "mean": float(np.mean(tfidf_coherences)),
                    "std": float(np.std(tfidf_coherences)),
                    "min": float(np.min(tfidf_coherences)),
                    "max": float(np.max(tfidf_coherences)),
                },
                "semantic_ranking_quality": {
                    "mean": float(np.mean(semantic_rankings)),
                    "std": float(np.std(semantic_rankings)) if len(semantic_rankings) > 1 else 0.0,
                },
                "tfidf_ranking_quality": {
                    "mean": float(np.mean(tfidf_rankings)),
                    "std": float(np.std(tfidf_rankings)) if len(tfidf_rankings) > 1 else 0.0,
                },
                "advantages": {
                    "coherence_improvement": float((np.mean(semantic_coherences) - np.mean(tfidf_coherences))),
                    "coherence_improvement_pct": float((np.mean(semantic_coherences) / np.mean(tfidf_coherences) - 1) * 100),
                    "ranking_quality_improvement": float(np.mean(semantic_rankings) - np.mean(tfidf_rankings)),
                    "semantic_diversity_advantage": float(np.mean(semantic_diversity) - np.mean(tfidf_diversity)),
                }
            }
        }
        
        output_path = os.path.join(os.path.dirname(__file__), 'evaluation_ranking_quality.json')
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Ranking quality evaluation saved to: {output_path}")
        return output


async def main():
    async with async_session_maker() as db:
        evaluator = RankingQualityEvaluator(db)
        await evaluator.run_evaluation()


if __name__ == "__main__":
    asyncio.run(main())
