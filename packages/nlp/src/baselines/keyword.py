"""
Keyword Matcher

Simple keyword-based matching using NLTK for baseline comparison.
"""

from typing import List, Set, Tuple

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


class KeywordMatcher:
    """
    Simple keyword matching baseline.
    
    Uses exact keyword overlap for similarity with NLTK tokenization.
    """
    
    def __init__(
        self, 
        stopwords_set: Set[str] = None,
        language: str = "english",
        min_word_length: int = 2,
    ):
        """
        Initialize keyword matcher.
        
        Args:
            stopwords_set: Custom set of stopwords (uses NLTK stopwords if None)
            language: Language for NLTK stopwords
            min_word_length: Minimum word length to consider
        """
        self.language = language
        self.min_word_length = min_word_length
        
        if stopwords_set is not None:
            self.stopwords = stopwords_set
        else:
            self.stopwords = set(stopwords.words(language))
        
        self._corpus_keywords = None
        self._is_fitted = False
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text using NLTK tokenization."""
        tokens = word_tokenize(text.lower())
        return {
            t for t in tokens 
            if t.isalnum() 
            and t not in self.stopwords 
            and len(t) >= self.min_word_length
        }
    
    def fit(self, corpus: List[str]) -> "KeywordMatcher":
        """
        Fit on a corpus.
        
        Args:
            corpus: List of documents
            
        Returns:
            Self for chaining
        """
        self._corpus_keywords = [self._extract_keywords(doc) for doc in corpus]
        self._is_fitted = True
        return self
    
    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        Search for documents with matching keywords.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            List of (index, score) tuples
        """
        if not self._is_fitted:
            raise ValueError("Must call fit() before search()")
        
        query_keywords = self._extract_keywords(query)
        
        if not query_keywords:
            return []
        
        scores = []
        for idx, doc_keywords in enumerate(self._corpus_keywords):
            if not doc_keywords:
                scores.append((idx, 0.0))
                continue
            
            # Jaccard similarity
            intersection = len(query_keywords & doc_keywords)
            union = len(query_keywords | doc_keywords)
            score = intersection / union if union > 0 else 0.0
            
            scores.append((idx, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
