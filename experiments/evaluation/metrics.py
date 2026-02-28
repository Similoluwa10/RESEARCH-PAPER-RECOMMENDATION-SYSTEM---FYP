"""
Evaluation Metrics

Implementation of information retrieval evaluation metrics.
"""

from typing import List, Dict
import numpy as np


def precision_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    """
    Calculate Precision@K.
    
    Args:
        relevant: List of relevant item IDs
        retrieved: List of retrieved item IDs (in order)
        k: Number of top items to consider
        
    Returns:
        Precision@K score
    """
    if k <= 0 or not retrieved:
        return 0.0
    
    retrieved_k = retrieved[:k]
    relevant_set = set(relevant)
    
    relevant_retrieved = sum(1 for item in retrieved_k if item in relevant_set)
    
    return relevant_retrieved / k


def recall_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    """
    Calculate Recall@K.
    
    Args:
        relevant: List of relevant item IDs
        retrieved: List of retrieved item IDs (in order)
        k: Number of top items to consider
        
    Returns:
        Recall@K score
    """
    if not relevant or not retrieved:
        return 0.0
    
    retrieved_k = retrieved[:k]
    relevant_set = set(relevant)
    
    relevant_retrieved = sum(1 for item in retrieved_k if item in relevant_set)
    
    return relevant_retrieved / len(relevant)


def f1_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    """
    Calculate F1@K.
    
    Args:
        relevant: List of relevant item IDs
        retrieved: List of retrieved item IDs (in order)
        k: Number of top items to consider
        
    Returns:
        F1@K score
    """
    p = precision_at_k(relevant, retrieved, k)
    r = recall_at_k(relevant, retrieved, k)
    
    if p + r == 0:
        return 0.0
    
    return 2 * (p * r) / (p + r)


def average_precision(relevant: List[str], retrieved: List[str]) -> float:
    """
    Calculate Average Precision.
    
    Args:
        relevant: List of relevant item IDs
        retrieved: List of retrieved item IDs (in order)
        
    Returns:
        Average Precision score
    """
    if not relevant or not retrieved:
        return 0.0
    
    relevant_set = set(relevant)
    precisions = []
    relevant_count = 0
    
    for i, item in enumerate(retrieved):
        if item in relevant_set:
            relevant_count += 1
            precisions.append(relevant_count / (i + 1))
    
    if not precisions:
        return 0.0
    
    return sum(precisions) / len(relevant)


def mean_average_precision(
    relevants: List[List[str]],
    retrieveds: List[List[str]],
) -> float:
    """
    Calculate Mean Average Precision (MAP).
    
    Args:
        relevants: List of relevant item lists (one per query)
        retrieveds: List of retrieved item lists (one per query)
        
    Returns:
        MAP score
    """
    if not relevants or not retrieveds:
        return 0.0
    
    aps = [
        average_precision(rel, ret)
        for rel, ret in zip(relevants, retrieveds)
    ]
    
    return np.mean(aps)


def reciprocal_rank(relevant: List[str], retrieved: List[str]) -> float:
    """
    Calculate Reciprocal Rank.
    
    Args:
        relevant: List of relevant item IDs
        retrieved: List of retrieved item IDs (in order)
        
    Returns:
        Reciprocal Rank score
    """
    relevant_set = set(relevant)
    
    for i, item in enumerate(retrieved):
        if item in relevant_set:
            return 1.0 / (i + 1)
    
    return 0.0


def mean_reciprocal_rank(
    relevants: List[List[str]],
    retrieveds: List[List[str]],
) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).
    
    Args:
        relevants: List of relevant item lists (one per query)
        retrieveds: List of retrieved item lists (one per query)
        
    Returns:
        MRR score
    """
    if not relevants or not retrieveds:
        return 0.0
    
    rrs = [
        reciprocal_rank(rel, ret)
        for rel, ret in zip(relevants, retrieveds)
    ]
    
    return np.mean(rrs)


def dcg_at_k(relevances: List[float], k: int) -> float:
    """
    Calculate Discounted Cumulative Gain at K.
    
    Args:
        relevances: List of relevance scores (in retrieved order)
        k: Number of top items to consider
        
    Returns:
        DCG@K score
    """
    relevances = np.array(relevances[:k])
    
    if len(relevances) == 0:
        return 0.0
    
    # Using log2(i+2) for positions starting from 0
    discounts = np.log2(np.arange(2, len(relevances) + 2))
    
    return np.sum(relevances / discounts)


def ndcg_at_k(relevances: List[float], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.
    
    Args:
        relevances: List of relevance scores (in retrieved order)
        k: Number of top items to consider
        
    Returns:
        NDCG@K score
    """
    dcg = dcg_at_k(relevances, k)
    
    # Ideal DCG (sorted by relevance)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal_relevances, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def compute_all_metrics(
    relevant: List[str],
    retrieved: List[str],
    k_values: List[int] = [1, 3, 5, 10, 20],
) -> Dict[str, float]:
    """
    Compute all evaluation metrics.
    
    Args:
        relevant: List of relevant item IDs
        retrieved: List of retrieved item IDs (in order)
        k_values: K values to compute metrics for
        
    Returns:
        Dictionary of metric name -> score
    """
    results = {}
    
    for k in k_values:
        results[f"precision@{k}"] = precision_at_k(relevant, retrieved, k)
        results[f"recall@{k}"] = recall_at_k(relevant, retrieved, k)
        results[f"f1@{k}"] = f1_at_k(relevant, retrieved, k)
    
    results["map"] = average_precision(relevant, retrieved)
    results["mrr"] = reciprocal_rank(relevant, retrieved)
    
    return results
