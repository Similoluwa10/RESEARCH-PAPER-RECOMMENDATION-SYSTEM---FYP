"""
Benchmark Suite

Run comprehensive benchmarks comparing recommendation methods.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List

import yaml

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages', 'nlp'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages', 'shared'))

from src.embeddings import SentenceTransformerEmbedding
from src.baselines import TFIDFBaseline, BM25Baseline, KeywordMatcher
from src.similarity import CosineSimilarity

from metrics import (
    precision_at_k,
    recall_at_k,
    f1_at_k,
    mean_average_precision,
    mean_reciprocal_rank,
    ndcg_at_k,
)


class BenchmarkRunner:
    """Run benchmarks comparing different recommendation methods."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize benchmark runner.
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config = self._load_config(config_path)
        self.results = {}
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "methods": ["semantic", "tfidf", "bm25", "keyword"],
            "k_values": [1, 3, 5, 10, 20],
            "embedding_model": "all-MiniLM-L6-v2",
        }
    
    def run_semantic_search(
        self,
        queries: List[str],
        corpus: List[str],
        top_k: int = 10,
    ) -> List[List[int]]:
        """Run semantic search using sentence transformers."""
        embedder = SentenceTransformerEmbedding(self.config["embedding_model"])
        
        # Generate embeddings
        query_embeddings = embedder.encode_batch(queries)
        corpus_embeddings = embedder.encode_batch(corpus)
        
        # Find top-k for each query
        results = []
        for query_emb in query_embeddings:
            top_indices = CosineSimilarity.top_k(query_emb, corpus_embeddings, top_k)
            results.append([idx for idx, _ in top_indices])
        
        return results
    
    def run_tfidf_search(
        self,
        queries: List[str],
        corpus: List[str],
        top_k: int = 10,
    ) -> List[List[int]]:
        """Run TF-IDF based search."""
        tfidf = TFIDFBaseline()
        tfidf.fit(corpus)
        
        results = []
        for query in queries:
            top_results = tfidf.search(query, top_k=top_k)
            results.append([idx for idx, _ in top_results])
        
        return results
    
    def run_bm25_search(
        self,
        queries: List[str],
        corpus: List[str],
        top_k: int = 10,
    ) -> List[List[int]]:
        """Run BM25 based search."""
        bm25 = BM25Baseline()
        bm25.fit(corpus)
        
        results = []
        for query in queries:
            top_results = bm25.search(query, top_k=top_k)
            results.append([idx for idx, _ in top_results])
        
        return results
    
    def evaluate_method(
        self,
        method_name: str,
        retrieved: List[List[str]],
        relevant: List[List[str]],
    ) -> Dict[str, float]:
        """Evaluate a retrieval method."""
        k_values = self.config["k_values"]
        
        metrics = {}
        
        for k in k_values:
            p_scores = [precision_at_k(rel, ret, k) for rel, ret in zip(relevant, retrieved)]
            r_scores = [recall_at_k(rel, ret, k) for rel, ret in zip(relevant, retrieved)]
            f1_scores = [f1_at_k(rel, ret, k) for rel, ret in zip(relevant, retrieved)]
            
            metrics[f"precision@{k}"] = sum(p_scores) / len(p_scores)
            metrics[f"recall@{k}"] = sum(r_scores) / len(r_scores)
            metrics[f"f1@{k}"] = sum(f1_scores) / len(f1_scores)
        
        metrics["map"] = mean_average_precision(relevant, retrieved)
        metrics["mrr"] = mean_reciprocal_rank(relevant, retrieved)
        
        return metrics
    
    def run_full_benchmark(
        self,
        queries: List[str],
        corpus: List[str],
        ground_truth: List[List[str]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Run full benchmark suite.
        
        Args:
            queries: List of query texts
            corpus: List of corpus documents
            ground_truth: List of relevant document IDs per query
            
        Returns:
            Dictionary of method -> metrics
        """
        results = {}
        max_k = max(self.config["k_values"])
        
        for method in self.config["methods"]:
            print(f"Running {method} search...")
            
            if method == "semantic":
                retrieved_indices = self.run_semantic_search(queries, corpus, max_k)
            elif method == "tfidf":
                retrieved_indices = self.run_tfidf_search(queries, corpus, max_k)
            elif method == "bm25":
                retrieved_indices = self.run_bm25_search(queries, corpus, max_k)
            else:
                continue
            
            # Convert indices to IDs
            retrieved = [[str(idx) for idx in indices] for indices in retrieved_indices]
            
            results[method] = self.evaluate_method(method, retrieved, ground_truth)
        
        self.results = results
        return results
    
    def save_results(self, output_path: str = None):
        """Save benchmark results to JSON file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"results/benchmark_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump({
                "config": self.config,
                "results": self.results,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)
        
        print(f"Results saved to {output_path}")
    
    def print_summary(self):
        """Print results summary."""
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        
        for method, metrics in self.results.items():
            print(f"\n{method.upper()}")
            print("-" * 40)
            for metric, value in sorted(metrics.items()):
                print(f"  {metric}: {value:.4f}")


if __name__ == "__main__":
    # Example usage
    print("Benchmark runner ready.")
    print("Usage: runner = BenchmarkRunner(config_path)")
    print("       runner.run_full_benchmark(queries, corpus, ground_truth)")
