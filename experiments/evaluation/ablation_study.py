"""
Ablation Study

Analyze the impact of different components on recommendation quality.
"""

import json
import os
from datetime import datetime
from typing import Dict, List

from benchmark import BenchmarkRunner
from metrics import compute_all_metrics


class AblationStudy:
    """
    Conduct ablation studies to understand component contributions.
    
    Tests variations of the recommendation system to identify
    which components contribute most to performance.
    """
    
    def __init__(self):
        self.results = {}
    
    def run_embedding_model_comparison(
        self,
        queries: List[str],
        corpus: List[str],
        ground_truth: List[List[str]],
        models: List[str] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare different embedding models.
        
        Args:
            queries: List of query texts
            corpus: List of corpus documents
            ground_truth: Relevant docs per query
            models: List of model names to test
            
        Returns:
            Results for each model
        """
        if models is None:
            models = [
                "all-MiniLM-L6-v2",      # Fast, good quality
                "all-mpnet-base-v2",      # Higher quality
                "paraphrase-MiniLM-L6-v2", # Paraphrase focused
            ]
        
        results = {}
        
        for model in models:
            print(f"Testing model: {model}")
            
            config = {"embedding_model": model, "k_values": [5, 10, 20]}
            runner = BenchmarkRunner()
            runner.config = config
            
            retrieved = runner.run_semantic_search(queries, corpus, top_k=20)
            retrieved_ids = [[str(idx) for idx in indices] for indices in retrieved]
            
            metrics = runner.evaluate_method(model, retrieved_ids, ground_truth)
            results[model] = metrics
        
        self.results["embedding_models"] = results
        return results
    
    def run_preprocessing_ablation(
        self,
        queries: List[str],
        corpus: List[str],
        ground_truth: List[List[str]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Test impact of different preprocessing steps.
        
        Args:
            queries: List of query texts
            corpus: List of corpus documents
            ground_truth: Relevant docs per query
            
        Returns:
            Results for each preprocessing configuration
        """
        from src.preprocessing import TextCleaner
        
        configurations = {
            "no_preprocessing": {},
            "lowercase_only": {"lowercase": True},
            "remove_urls": {"remove_urls": True},
            "full_cleaning": {
                "lowercase": True,
                "remove_urls": True,
                "remove_special_chars": True,
            },
        }
        
        results = {}
        
        for config_name, config in configurations.items():
            print(f"Testing preprocessing: {config_name}")
            
            cleaner = TextCleaner(**config)
            cleaned_queries = cleaner.clean_batch(queries)
            cleaned_corpus = cleaner.clean_batch(corpus)
            
            runner = BenchmarkRunner()
            retrieved = runner.run_semantic_search(cleaned_queries, cleaned_corpus, top_k=20)
            retrieved_ids = [[str(idx) for idx in indices] for indices in retrieved]
            
            metrics = runner.evaluate_method(config_name, retrieved_ids, ground_truth)
            results[config_name] = metrics
        
        self.results["preprocessing"] = results
        return results
    
    def run_hybrid_weight_ablation(
        self,
        queries: List[str],
        corpus: List[str],
        ground_truth: List[List[str]],
        weights: List[float] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Test different weights for hybrid search.
        
        Args:
            queries: List of query texts
            corpus: List of corpus documents
            ground_truth: Relevant docs per query
            weights: List of semantic weights to test (keyword weight = 1 - semantic)
            
        Returns:
            Results for each weight configuration
        """
        if weights is None:
            weights = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        results = {}
        
        runner = BenchmarkRunner()
        
        # Get base results
        semantic_results = runner.run_semantic_search(queries, corpus, top_k=50)
        tfidf_results = runner.run_tfidf_search(queries, corpus, top_k=50)
        
        for semantic_weight in weights:
            config_name = f"semantic_{semantic_weight:.2f}"
            print(f"Testing weight: {config_name}")
            
            keyword_weight = 1 - semantic_weight
            
            # Combine results (simplified fusion)
            # In practice, you'd use proper score fusion
            hybrid_results = []
            for sem, tfidf in zip(semantic_results, tfidf_results):
                # Simple interleaving based on weights
                combined = []
                sem_idx, tfidf_idx = 0, 0
                
                while len(combined) < 20:
                    if sem_idx < len(sem) and (
                        tfidf_idx >= len(tfidf) or 
                        len(combined) % 2 == 0
                    ):
                        if sem[sem_idx] not in combined:
                            combined.append(sem[sem_idx])
                        sem_idx += 1
                    elif tfidf_idx < len(tfidf):
                        if tfidf[tfidf_idx] not in combined:
                            combined.append(tfidf[tfidf_idx])
                        tfidf_idx += 1
                    else:
                        break
                
                hybrid_results.append(combined)
            
            retrieved_ids = [[str(idx) for idx in indices] for indices in hybrid_results]
            metrics = runner.evaluate_method(config_name, retrieved_ids, ground_truth)
            results[config_name] = metrics
        
        self.results["hybrid_weights"] = results
        return results
    
    def save_results(self, output_path: str = None):
        """Save ablation study results."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"results/ablation_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump({
                "results": self.results,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)
        
        print(f"Ablation results saved to {output_path}")


if __name__ == "__main__":
    print("Ablation study module ready.")
    print("Usage: study = AblationStudy()")
    print("       study.run_embedding_model_comparison(queries, corpus, ground_truth)")
