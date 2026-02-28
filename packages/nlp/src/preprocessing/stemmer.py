"""
Stemmer and Lemmatizer

Text normalization through stemming and lemmatization using NLTK.
"""

from typing import List, Literal

import nltk
from nltk.stem import PorterStemmer, SnowballStemmer, LancasterStemmer
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)


StemmerType = Literal["porter", "snowball", "lancaster"]


class TextStemmer:
    """NLTK-based stemmer for text normalization."""
    
    def __init__(
        self,
        stemmer_type: StemmerType = "porter",
        language: str = "english",
    ):
        """
        Initialize stemmer.
        
        Args:
            stemmer_type: Type of stemmer ("porter", "snowball", "lancaster")
            language: Language for Snowball stemmer (default: "english")
        """
        self.stemmer_type = stemmer_type
        self.language = language
        
        if stemmer_type == "porter":
            self._stemmer = PorterStemmer()
        elif stemmer_type == "snowball":
            self._stemmer = SnowballStemmer(language)
        elif stemmer_type == "lancaster":
            self._stemmer = LancasterStemmer()
        else:
            raise ValueError(f"Unknown stemmer type: {stemmer_type}")
    
    def stem(self, word: str) -> str:
        """
        Stem a single word.
        
        Args:
            word: Input word
            
        Returns:
            Stemmed word
        """
        return self._stemmer.stem(word)
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """
        Stem a list of tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            List of stemmed tokens
        """
        return [self.stem(token) for token in tokens]
    
    def stem_text(self, text: str) -> str:
        """
        Stem all words in a text string.
        
        Args:
            text: Input text
            
        Returns:
            Text with stemmed words
        """
        words = text.split()
        stemmed = [self.stem(word) for word in words]
        return ' '.join(stemmed)
    
    @staticmethod
    def available_snowball_languages() -> List[str]:
        """Get available languages for Snowball stemmer."""
        return list(SnowballStemmer.languages)


class TextLemmatizer:
    """NLTK-based lemmatizer for text normalization."""
    
    def __init__(self):
        """Initialize WordNet lemmatizer."""
        self._lemmatizer = WordNetLemmatizer()
    
    def lemmatize(self, word: str, pos: str = "n") -> str:
        """
        Lemmatize a single word.
        
        Args:
            word: Input word
            pos: Part of speech tag ('n'=noun, 'v'=verb, 'a'=adjective, 'r'=adverb)
            
        Returns:
            Lemmatized word
        """
        return self._lemmatizer.lemmatize(word, pos)
    
    def lemmatize_tokens(
        self, 
        tokens: List[str], 
        pos: str = "n"
    ) -> List[str]:
        """
        Lemmatize a list of tokens.
        
        Args:
            tokens: List of tokens
            pos: Part of speech for all tokens
            
        Returns:
            List of lemmatized tokens
        """
        return [self.lemmatize(token, pos) for token in tokens]
    
    def lemmatize_with_pos(self, tokens: List[str]) -> List[str]:
        """
        Lemmatize tokens using automatic POS tagging.
        
        Args:
            tokens: List of tokens
            
        Returns:
            List of lemmatized tokens
        """
        # Get POS tags
        pos_tags = nltk.pos_tag(tokens)
        
        lemmatized = []
        for word, tag in pos_tags:
            # Convert Penn Treebank tags to WordNet tags
            wn_tag = self._get_wordnet_pos(tag)
            if wn_tag:
                lemmatized.append(self._lemmatizer.lemmatize(word, wn_tag))
            else:
                lemmatized.append(self._lemmatizer.lemmatize(word))
        
        return lemmatized
    
    def lemmatize_text(self, text: str, use_pos: bool = True) -> str:
        """
        Lemmatize all words in a text string.
        
        Args:
            text: Input text
            use_pos: Whether to use POS tagging for better lemmatization
            
        Returns:
            Text with lemmatized words
        """
        words = text.split()
        
        if use_pos:
            lemmatized = self.lemmatize_with_pos(words)
        else:
            lemmatized = self.lemmatize_tokens(words)
        
        return ' '.join(lemmatized)
    
    @staticmethod
    def _get_wordnet_pos(treebank_tag: str) -> str:
        """
        Convert Penn Treebank POS tag to WordNet POS tag.
        
        Args:
            treebank_tag: Penn Treebank POS tag
            
        Returns:
            WordNet POS tag or empty string
        """
        if treebank_tag.startswith('J'):
            return 'a'  # adjective
        elif treebank_tag.startswith('V'):
            return 'v'  # verb
        elif treebank_tag.startswith('N'):
            return 'n'  # noun
        elif treebank_tag.startswith('R'):
            return 'r'  # adverb
        else:
            return ''
