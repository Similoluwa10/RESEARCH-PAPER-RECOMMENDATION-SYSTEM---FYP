"""
Evaluation Metrics

Constants for evaluation metrics used in experiments.
"""

# Information Retrieval Metrics
IR_METRICS = {
    "precision_at_k": {
        "name": "Precision@K",
        "description": "Fraction of recommended items that are relevant",
        "range": (0, 1),
        "higher_is_better": True,
    },
    "recall_at_k": {
        "name": "Recall@K",
        "description": "Fraction of relevant items that are recommended",
        "range": (0, 1),
        "higher_is_better": True,
    },
    "f1_at_k": {
        "name": "F1@K",
        "description": "Harmonic mean of Precision@K and Recall@K",
        "range": (0, 1),
        "higher_is_better": True,
    },
    "map": {
        "name": "Mean Average Precision (MAP)",
        "description": "Mean of average precision across all queries",
        "range": (0, 1),
        "higher_is_better": True,
    },
    "mrr": {
        "name": "Mean Reciprocal Rank (MRR)",
        "description": "Average reciprocal rank of first relevant item",
        "range": (0, 1),
        "higher_is_better": True,
    },
    "ndcg_at_k": {
        "name": "NDCG@K",
        "description": "Normalized Discounted Cumulative Gain",
        "range": (0, 1),
        "higher_is_better": True,
    },
}

# Default K values for evaluation
DEFAULT_K_VALUES = [1, 3, 5, 10, 20]

# Similarity metrics
SIMILARITY_METRICS = {
    "cosine": "Cosine Similarity",
    "euclidean": "Euclidean Distance",
    "dot_product": "Dot Product",
}

# Methods to compare
RECOMMENDATION_METHODS = {
    "semantic": "Semantic Search (Sentence Transformers)",
    "tfidf": "TF-IDF Baseline",
    "bm25": "BM25 Baseline",
    "keyword": "Keyword Matching",
    "hybrid": "Hybrid (Semantic + Keyword)",
}
