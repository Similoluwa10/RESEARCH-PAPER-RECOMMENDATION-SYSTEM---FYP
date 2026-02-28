"""
BM25 Baseline

BM25 ranking algorithm for text retrieval using NLTK.
"""

import math
from collections import Counter
from typing import List, Tuple, Set

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


class BM25Baseline:
    """
    BM25 (Best Match 25) ranking baseline.
    
    A probabilistic ranking function used in information retrieval.
    Uses NLTK for tokenization and stopword filtering.
    """
    
    def __init__(
        self, 
        k1: float = 1.5, 
        b: float = 0.75,
        use_stopwords: bool = True,
        language: str = "english",
    ):
        """
        Initialize BM25.
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
            use_stopwords: Whether to filter stopwords
            language: Language for stopwords
        """
        self.k1 = k1
        self.b = b
        self.use_stopwords = use_stopwords
        self.language = language
        
        self._stopwords: Set[str] = set()
        if use_stopwords:
            self._stopwords = set(stopwords.words(language))
        
        self._corpus = None
        self._doc_freqs = None
        self._doc_lengths = None
        self._avg_doc_length = 0
        self._num_docs = 0
        self._is_fitted = False
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text using NLTK word_tokenize."""
        tokens = word_tokenize(text.lower())
        # Filter: keep alphanumeric tokens, remove stopwords
        tokens = [
            t for t in tokens 
            if t.isalnum() and t not in self._stopwords
        ]
        return tokens
    
    def fit(self, corpus: List[str]) -> "BM25Baseline":
        """
        Fit BM25 on a corpus.
        
        Args:
            corpus: List of documents
            
        Returns:
            Self for chaining
        """
        self._corpus = [self._tokenize(doc) for doc in corpus]
        self._num_docs = len(corpus)
        
        # Compute document frequencies
        self._doc_freqs = Counter()
        for doc in self._corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self._doc_freqs[term] += 1
        
        # Compute document lengths
        self._doc_lengths = [len(doc) for doc in self._corpus]
        self._avg_doc_length = sum(self._doc_lengths) / len(self._doc_lengths)
        
        self._is_fitted = True
        return self
    
    def _idf(self, term: str) -> float:
        """Compute IDF for a term."""
        df = self._doc_freqs.get(term, 0)
        return math.log((self._num_docs - df + 0.5) / (df + 0.5) + 1)
    
    def _score(self, query_terms: List[str], doc_idx: int) -> float:
        """Compute BM25 score for a document."""
        doc = self._corpus[doc_idx]
        doc_len = self._doc_lengths[doc_idx]
        
        term_freqs = Counter(doc)
        score = 0.0
        
        for term in query_terms:
            if term not in term_freqs:
                continue
            
            tf = term_freqs[term]
            idf = self._idf(term)
            
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_doc_length)
            
            score += idf * numerator / denominator
        
        return score
    
    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        Search for relevant documents.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            List of (index, score) tuples
        """
        if not self._is_fitted:
            raise ValueError("Must call fit() before search()")
        
        query_terms = self._tokenize(query)
        
        scores = []
        for doc_idx in range(self._num_docs):
            score = self._score(query_terms, doc_idx)
            scores.append((doc_idx, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
