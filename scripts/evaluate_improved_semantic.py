"""
Improved Semantic vs TF-IDF Evaluation
Uses domain-specific embeddings (SPECTER) and query processing improvements.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages'))

from src.services.search_service import SearchService
from src.schemas.search import SearchRequest, SearchMethod
from src.models.base import async_session_maker
from nlp.src.query_processor import QueryProcessor
from nlp.src.domain_embeddings import DomainEmbeddingModel


class ImprovedSemanticEvaluator:
    """Evaluation using improved embeddings and query processing."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.search_service = SearchService(db_session)
        
        # Initialize domain embeddings (SPECTER for academic papers)
        logger_msg = "Initializing domain-specific embeddings (SPECTER)..."
        print(f"\n{logger_msg}")
        self.embedding_model = DomainEmbeddingModel("allenai/specter")
        
        # Initialize query processor for improvements
        print("Initializing query processor for semantic expansion...")
        self.query_processor = QueryProcessor()
        
        # Test queries
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
    
    async def evaluate_query(self, query: str, semantic_query_variant: str) -> Dict:
        """Evaluate single query with improvements."""
        
        # Get semantic coherence using domain embeddings
        query_embedding = self.embedding_model.encode(semantic_query_variant)
        
        # Process query: expand and rewrite for better semantic matching
        expanded_query, rewritten_query = self.query_processor.process_for_semantic_search(query)
        
        # Semantic search with improved embeddings
        semantic_request = SearchRequest(
            query=rewritten_query,  # Use rewritten query for better semantic understanding
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
        
        # TF-IDF search (baseline)
        tfidf_request = SearchRequest(
            query=expanded_query,  # Use expanded query for better coverage
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
        
        # Calculate semantic coherence for both methods
        semantic_coherence = self._calculate_coherence(query_embedding, semantic_results)
        tfidf_coherence = self._calculate_coherence(query_embedding, tfidf_results)
        
        # Diversity check
        semantic_diversity = len(set(r['id'] for r in semantic_results)) / len(semantic_results)
        tfidf_diversity = len(set(r['id'] for r in tfidf_results)) / len(tfidf_results)
        
        return {
            "query": query,
            "semantic_variant": semantic_query_variant,
            "query_processing": {
                "original": query,
                "expanded": expanded_query,
                "rewritten": rewritten_query,
            },
            "semantic_search": {
                "coherence": float(semantic_coherence),
                "diversity": float(semantic_diversity),
                "results_count": len(semantic_results),
                "top_3_titles": [r['title'] for r in semantic_results[:3]],
            },
            "tfidf_search": {
                "coherence": float(tfidf_coherence),
                "diversity": float(tfidf_diversity),
                "results_count": len(tfidf_results),
                "top_3_titles": [r['title'] for r in tfidf_results[:3]],
            },
            "advantage": {
                "coherence_improvement": float(semantic_coherence - tfidf_coherence),
                "coherence_improvement_pct": float((semantic_coherence / tfidf_coherence - 1) * 100) if tfidf_coherence > 0 else 0,
                "diversity_advantage": float(semantic_diversity - tfidf_diversity),
            }
        }
    
    def _calculate_coherence(self, query_embedding: np.ndarray, results: List[Dict]) -> float:
        """Calculate semantic coherence of results."""
        if not results:
            return 0.0
        
        coherence_scores = []
        for result in results:
            title = result.get('title', '')
            abstract = result.get('abstract', '')
            text = f"{title}. {abstract}"[:512]
            
            result_embedding = self.embedding_model.encode(text)
            
            # Cosine similarity
            similarity = np.dot(query_embedding, result_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(result_embedding) + 1e-8
            )
            coherence_scores.append(float(similarity))
        
        return np.mean(coherence_scores) if coherence_scores else 0.0
    
    async def run_evaluation(self) -> Dict:
        """Run complete evaluation."""
        print("\n" + "="*80)
        print("IMPROVED SEMANTIC VS TF-IDF EVALUATION")
        print("="*80)
        print("Using: Domain-Specific Embeddings (SPECTER) + Query Processing")
        print("="*80 + "\n")
        
        results = []
        
        for i, (query, semantic_variant) in enumerate(self.test_queries, 1):
            print(f"[{i}/10] Evaluating: '{query}'")
            try:
                query_result = await self.evaluate_query(query, semantic_variant)
                results.append(query_result)
                
                sem_coh = query_result['semantic_search']['coherence']
                tfidf_coh = query_result['tfidf_search']['coherence']
                adv = query_result['advantage']['coherence_improvement_pct']
                
                print(f"  Semantic Coherence: {sem_coh:.4f}")
                print(f"  TF-IDF Coherence:   {tfidf_coh:.4f}")
                print(f"  Improvement: {adv:+.1f}%\n")
            except Exception as e:
                print(f"  Error: {str(e)}\n")
                continue
        
        # Aggregate results
        print("\n" + "="*80)
        print("AGGREGATED RESULTS")
        print("="*80)
        
        semantic_coherences = [r['semantic_search']['coherence'] for r in results]
        tfidf_coherences = [r['tfidf_search']['coherence'] for r in results]
        
        sem_mean = np.mean(semantic_coherences)
        tfidf_mean = np.mean(tfidf_coherences)
        improvement = ((sem_mean / tfidf_mean - 1) * 100) if tfidf_mean > 0 else 0
        
        print(f"\n📊 SEMANTIC COHERENCE (Higher = Better)")
        print(f"  Semantic:  {sem_mean:.4f} ± {np.std(semantic_coherences):.4f}")
        print(f"  TF-IDF:    {tfidf_mean:.4f} ± {np.std(tfidf_coherences):.4f}")
        print(f"  Improvement: {improvement:+.1f}%")
        
        if improvement > 0:
            print(f"  ✓ SEMANTIC OUTPERFORMS TF-IDF with domain-specific embeddings!")
        else:
            print(f"  Note: Further optimization may be needed")
        
        # Save results
        output = {
            "timestamp": datetime.now().isoformat(),
            "evaluation_type": "improved_semantic",
            "methodology": "Domain-specific embeddings (SPECTER) + Query Processing",
            "improvements": [
                "SPECTER model for academic paper embeddings",
                "Query expansion with domain terminology",
                "Semantic query rewriting for better intent capture",
            ],
            "queries_evaluated": len(results),
            "per_query_results": results,
            "aggregated_metrics": {
                "semantic_coherence": {
                    "mean": float(sem_mean),
                    "std": float(np.std(semantic_coherences)),
                    "min": float(np.min(semantic_coherences)),
                    "max": float(np.max(semantic_coherences)),
                },
                "tfidf_coherence": {
                    "mean": float(tfidf_mean),
                    "std": float(np.std(tfidf_coherences)),
                    "min": float(np.min(tfidf_coherences)),
                    "max": float(np.max(tfidf_coherences)),
                },
                "improvement": {
                    "percentage": float(improvement),
                    "absolute_coherence_gain": float(sem_mean - tfidf_mean),
                }
            }
        }
        
        output_path = os.path.join(os.path.dirname(__file__), 'evaluation_improved.json')
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_path}")
        return output


async def main():
    async with async_session_maker() as db:
        evaluator = ImprovedSemanticEvaluator(db)
        await evaluator.run_evaluation()


if __name__ == "__main__":
    asyncio.run(main())
