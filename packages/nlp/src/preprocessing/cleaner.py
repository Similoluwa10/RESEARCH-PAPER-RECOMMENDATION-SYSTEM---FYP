"""
Text Cleaner

Text cleaning and normalization utilities with NLTK support.
"""

import re
from typing import List

import nltk
from nltk.tokenize import word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)


class TextCleaner:
    """Clean and normalize text for NLP processing."""
    
    def __init__(
        self,
        lowercase: bool = True,
        remove_urls: bool = True,
        remove_emails: bool = True,
        remove_special_chars: bool = False,
        remove_numbers: bool = False,
        remove_punctuation: bool = False,
    ):
        """
        Initialize text cleaner.
        
        Args:
            lowercase: Convert to lowercase
            remove_urls: Remove URL patterns
            remove_emails: Remove email addresses
            remove_special_chars: Remove special characters
            remove_numbers: Remove numeric values
            remove_punctuation: Remove punctuation marks
        """
        self.lowercase = lowercase
        self.remove_urls = remove_urls
        self.remove_emails = remove_emails
        self.remove_special_chars = remove_special_chars
        self.remove_numbers = remove_numbers
        self.remove_punctuation = remove_punctuation
    
    def clean(self, text: str) -> str:
        """
        Clean a text string.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove URLs
        if self.remove_urls:
            text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove emails
        if self.remove_emails:
            text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters (keep alphanumeric and spaces)
        if self.remove_special_chars:
            text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        
        # Remove numbers
        if self.remove_numbers:
            text = re.sub(r'\d+', '', text)
        
        # Remove punctuation using NLTK tokenization
        if self.remove_punctuation:
            tokens = word_tokenize(text)
            tokens = [t for t in tokens if t.isalnum()]
            text = ' '.join(tokens)
        
        # Lowercase
        if self.lowercase:
            text = text.lower()
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def clean_batch(self, texts: List[str]) -> List[str]:
        """Clean multiple texts."""
        return [self.clean(text) for text in texts]
    
    @staticmethod
    def remove_latex(text: str) -> str:
        """Remove LaTeX math expressions."""
        # Remove inline math
        text = re.sub(r'\$[^$]+\$', '', text)
        # Remove display math
        text = re.sub(r'\\\[.*?\\\]', '', text, flags=re.DOTALL)
        text = re.sub(r'\\\(.*?\\\)', '', text, flags=re.DOTALL)
        return text
    
    @staticmethod
    def remove_citations(text: str) -> str:
        """Remove citation markers like [1], [2,3], etc."""
        return re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
