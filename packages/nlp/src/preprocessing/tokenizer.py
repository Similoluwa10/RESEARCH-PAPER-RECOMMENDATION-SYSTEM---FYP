"""
Tokenizer

Text tokenization utilities using NLTK.
"""

from typing import List, Set

import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Download required NLTK data (silently if already present)
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


class Tokenizer:
    """NLTK-based tokenizer for text processing."""
    
    def __init__(
        self,
        lowercase: bool = True,
        min_length: int = 2,
        stopwords_set: Set[str] = None,
        language: str = "english",
    ):
        """
        Initialize tokenizer.
        
        Args:
            lowercase: Convert tokens to lowercase
            min_length: Minimum token length
            stopwords_set: Custom set of stopwords (uses NLTK stopwords if None)
            language: Language for NLTK stopwords (default: "english")
        """
        self.lowercase = lowercase
        self.min_length = min_length
        self.language = language
        
        if stopwords_set is not None:
            self.stopwords = stopwords_set
        else:
            self.stopwords = set(stopwords.words(language))
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words using NLTK word_tokenize.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Use NLTK word tokenization
        tokens = word_tokenize(text)
        
        # Apply filters
        if self.lowercase:
            tokens = [t.lower() for t in tokens]
        
        # Filter by length and stopwords
        tokens = [
            t for t in tokens
            if len(t) >= self.min_length 
            and t.lower() not in self.stopwords
            and t.isalnum()  # Keep only alphanumeric tokens
        ]
        
        return tokens
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """
        Tokenize text into sentences using NLTK sent_tokenize.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        return sent_tokenize(text, language=self.language)
    
    def tokenize_batch(self, texts: List[str]) -> List[List[str]]:
        """Tokenize multiple texts."""
        return [self.tokenize(text) for text in texts]
    
    @staticmethod
    def get_english_stopwords() -> Set[str]:
        """Get NLTK English stopwords."""
        return set(stopwords.words("english"))
    
    @staticmethod
    def get_stopwords(language: str = "english") -> Set[str]:
        """
        Get NLTK stopwords for a specific language.
        
        Args:
            language: Language name (e.g., "english", "french", "german")
            
        Returns:
            Set of stopwords
        """
        return set(stopwords.words(language))
    
    @staticmethod
    def available_languages() -> List[str]:
        """Get list of available languages for stopwords."""
        return stopwords.fileids()
