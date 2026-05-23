"""
LangChain-based Explainability Service

Generates detailed, reasoning-based explanations for recommendations
using LangChain LLMs with modern API patterns.
"""

import logging
from typing import Any, Dict, List, Optional

from src.config import settings

logger = logging.getLogger(__name__)


class LangChainExplainer:
    """
    Generate LLM-based explanations for recommendations.
    
    Uses multi-step reasoning for transparent, detailed explanations.
    Supports multiple LLM providers (OpenAI, Ollama, Anthropic, Groq).
    """
    
    def __init__(self):
        """Initialize LangChain with configured provider."""
        self.llm = None
        self.provider = settings.LANGCHAIN_PROVIDER.lower()
        self.temperature = settings.LANGCHAIN_TEMPERATURE
        
        try:
            self._initialize_llm()
            logger.info(f"LangChain initialized with provider: {self.provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {e}")
            self.llm = None
    
    def _initialize_llm(self):
        """Initialize LLM based on configured provider."""
        if self.provider == 'openai':
            from langchain_openai import ChatOpenAI
            
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set in environment")
            
            self.llm = ChatOpenAI(
                model=settings.LANGCHAIN_CHAT_MODEL,
                temperature=self.temperature,
                api_key=settings.OPENAI_API_KEY,
            )
        
        elif self.provider == 'ollama':
            from langchain_community.chat_models import ChatOllama
            
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=self.temperature,
            )
        
        elif self.provider == 'anthropic':
            from langchain_anthropic import ChatAnthropic
            
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            
            self.llm = ChatAnthropic(
                model="claude-3-sonnet-20240229",
                temperature=self.temperature,
                api_key=settings.ANTHROPIC_API_KEY,
            )
        
        elif self.provider == 'groq':
            from langchain_groq import ChatGroq
            
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not set in environment")
            
            self.llm = ChatGroq(
                model=settings.GROQ_MODEL,  # Configurable Groq model (gemma2-9b-it, llama-3.1-70b-versatile, etc.)
                temperature=self.temperature,
                api_key=settings.GROQ_API_KEY,
            )
        
        else:
            raise ValueError(f"Unsupported LangChain provider: {self.provider}")
    
    def generate_explanation(
        self,
        query: str,
        paper: Any,
        similarity_score: float,
        key_terms: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete LLM-based explanation.
        
        Args:
            query: User's search query
            paper: Recommended paper object
            similarity_score: Overall similarity score (0-1)
            key_terms: Pre-extracted key matching terms
            
        Returns:
            Explanation dict with summary, reasoning, and metadata
        """
        if not self.llm:
            return self._generate_fallback_explanation(
                query, paper, similarity_score, key_terms or []
            )
        
        key_terms = key_terms or []
        
        try:
            from langchain_core.messages import HumanMessage
            
            # Limit abstract length for token efficiency
            abstract = (paper.abstract or "")[:500]
            
            # Step 1: Generate reasoning steps
            reasoning_prompt = f"""Analyze why this paper is recommended for this research query.

Query: {query}
Recommended Paper: {paper.title}
Abstract Summary: {abstract}
Similarity Score: {similarity_score:.2%}

Provide step-by-step reasoning:
1. Main concepts in the query
2. How these concepts appear in the paper
3. Relevance assessment
4. Key matching terms

Be concise and structured."""
            
            reasoning_message = HumanMessage(content=reasoning_prompt)
            reasoning_result = self.llm.invoke([reasoning_message])
            reasoning_text = reasoning_result.content
            
            # Step 2: Generate summary explanation
            summary_prompt = f"""Explain why this paper is relevant in 2-3 sentences. Be direct and specific.

Query: {query}
Paper: {paper.title}
Key Concepts: {", ".join(key_terms) if key_terms else "semantic similarity"}

Do not use phrases like "This paper matches..." or "because this paper...". 
Go straight to the point about the connection and relevance."""
            
            summary_message = HumanMessage(content=summary_prompt)
            summary_result = self.llm.invoke([summary_message])
            summary_text = summary_result.content
            
            return {
                "summary": summary_text.strip(),
                "reasoning_steps": reasoning_text.strip(),
                "key_terms": key_terms,
                "confidence": self._assess_confidence(similarity_score),
            }
        
        except Exception as e:
            logger.error(f"LangChain explanation generation failed: {e}")
            # Re-raise so ExplanationService can catch and disable LLM for subsequent attempts
            raise
    
    def _assess_confidence(self, score: float) -> str:
        """Assess confidence level based on similarity score."""
        if score >= 0.75:
            return "high"
        elif score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _generate_fallback_explanation(
        self,
        query: str,
        paper: Any,
        similarity_score: float,
        key_terms: List[str],
    ) -> Dict[str, Any]:
        """Fallback explanation when LLM is unavailable."""
        confidence = self._assess_confidence(similarity_score)
        
        if key_terms:
            terms_str = ", ".join(key_terms[:3])
            summary = f"This paper is relevant due to shared concepts: {terms_str}."
        else:
            summary = f"This paper matches your search based on semantic similarity."
        
        return {
            "summary": summary,
            "reasoning_steps": f"Similarity Score: {similarity_score:.2%} | Confidence: {confidence}",
            "key_terms": key_terms,
            "confidence": confidence,
        }
    
    def is_available(self) -> bool:
        """Check if LLM is available and working."""
        return self.llm is not None
