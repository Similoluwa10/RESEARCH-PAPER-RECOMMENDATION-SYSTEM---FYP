"""
Tests for top_k=100 default and single-prompt explanation merging.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.schemas.recommendation import RecommendationRequest
from src.services.langchain_explainer import LangChainExplainer
from src.services.recommendation_service import RecommendationService


def _make_paper(
    title: str = "Automated Bug Localization",
    abstract: str = "Deep learning for bug prediction.",
):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        title=title,
        abstract=abstract,
        authors=["Alice Smith"],
        category="Software Testing",
        source="arXiv",
        year=2025,
        venue="ICSE",
        keywords=["bug localization", "deep learning"],
        doi=None,
        url=None,
        created_at=now,
        updated_at=now,
    )


def _create_service_with_mock_db() -> RecommendationService:
    with patch.object(LangChainExplainer, "_initialize_llm", return_value=None):
        return RecommendationService(MagicMock())


class TestTopKDefault:
    """Verify recommendation retrieval defaults to top_k=100."""

    def test_recommendation_request_defaults_top_k_to_100(self):
        req = RecommendationRequest(query_text="automated software testing")
        assert req.top_k == 100

        with pytest.raises(ValidationError):
            RecommendationRequest(query_text="automated software testing", top_k=0)

        with pytest.raises(ValidationError):
            RecommendationRequest(query_text="automated software testing", top_k=101)

    @pytest.mark.asyncio
    async def test_custom_top_k_uses_distinct_cache_entries(self):
        RecommendationService._result_cache.clear()
        service = _create_service_with_mock_db()
        service.embedding_service = MagicMock()
        service.embedding_service.encode_text.return_value = [0.1] * 384

        papers = [_make_paper(f"Paper {i}") for i in range(5)]
        service.repository = MagicMock()
        service.repository.search_by_embedding = AsyncMock(
            side_effect=[
                [{"paper": p, "score": 0.9} for p in papers[:2]],
                [{"paper": p, "score": 0.9} for p in papers[:5]],
            ]
        )

        first = await service.get_recommendations_for_text(
            text="defect prediction",
            include_explanations=False,
            top_k=2,
        )
        second = await service.get_recommendations_for_text(
            text="defect prediction",
            include_explanations=False,
            top_k=5,
        )

        assert first.total == 2
        assert second.total == 5
        assert service.repository.search_by_embedding.await_count == 2

    @pytest.mark.asyncio
    async def test_get_recommendations_for_text_uses_top_k_100(self):
        RecommendationService._result_cache.clear()
        service = _create_service_with_mock_db()

        service.embedding_service = MagicMock()
        service.embedding_service.encode_text.return_value = [0.1] * 384

        paper = _make_paper()
        service.repository = MagicMock()
        service.repository.search_by_embedding = AsyncMock(
            return_value=[{"paper": paper, "score": 0.88}]
        )

        response = await service.get_recommendations_for_text(
            text="automated bug localization",
            include_explanations=False,
        )

        service.repository.search_by_embedding.assert_awaited_once_with(
            embedding=[0.1] * 384,
            top_k=100,
            min_similarity=service.min_recommendation_similarity,
        )
        assert response.total == 1

    @pytest.mark.asyncio
    async def test_get_similar_papers_uses_top_k_100(self):
        RecommendationService._result_cache.clear()
        service = _create_service_with_mock_db()

        source_paper = _make_paper("Source Paper", "Source abstract")
        similar_paper = _make_paper("Similar Paper", "Similar abstract")

        service.repository = MagicMock()
        service.repository.get_by_id = AsyncMock(return_value=source_paper)
        service.repository.find_similar = AsyncMock(
            return_value=[{"paper": similar_paper, "score": 0.82}]
        )

        response = await service.get_similar_papers(
            paper_id=source_paper.id,
            include_explanations=False,
        )

        service.repository.find_similar.assert_awaited_once_with(
            paper_id=source_paper.id,
            top_k=100,
            min_similarity=service.min_recommendation_similarity,
        )
        assert response.total == 1


class TestSinglePromptExplanation:
    """Verify merged single-prompt explanation generation and parsing."""

    @pytest.mark.asyncio
    async def test_single_llm_call_per_recommendation(self):
        explainer = LangChainExplainer.__new__(LangChainExplainer)
        explainer.provider = "groq"
        explainer.temperature = 0.3
        explainer.llm = MagicMock()
        explainer.llm.ainvoke = AsyncMock(
            return_value=SimpleNamespace(
                content=(
                    "<reasoning>\n"
                    "1. Query focuses on bug prediction.\n"
                    "2. Paper applies neural models to defect detection.\n"
                    "3. Strong empirical overlap.\n"
                    "4. Key terms: bug, prediction.\n"
                    "</reasoning>\n\n"
                    "<summary>\n"
                    "This study evaluates neural defect prediction models directly relevant to your query on automated bug detection.\n"
                    "</summary>"
                )
            )
        )

        paper = _make_paper()
        result = await explainer.generate_explanation(
            query="automated bug prediction",
            paper=paper,
            similarity_score=0.84,
            key_terms=["bug", "prediction"],
        )

        # Must invoke the LLM exactly ONCE per recommendation
        explainer.llm.ainvoke.assert_awaited_once()
        sent_messages = explainer.llm.ainvoke.call_args[0][0]
        assert len(sent_messages) == 1
        prompt_text = sent_messages[0].content
        assert "<reasoning>" in prompt_text
        assert "<summary>" in prompt_text
        assert "automated bug prediction" in prompt_text

        assert "1. Query focuses on bug prediction." in result["reasoning_steps"]
        assert (
            result["summary"]
            == "This study evaluates neural defect prediction models directly relevant to your query on automated bug detection."
        )
        assert result["key_terms"] == ["bug", "prediction"]
        assert result["confidence"] == "high"

    def test_parse_explanation_fallback_formats(self):
        explainer = LangChainExplainer.__new__(LangChainExplainer)

        # Case 1: Markdown headers instead of XML tags
        md_response = (
            "### Reasoning\n"
            "1. Shared focus on CI/CD pipelines.\n"
            "### Summary\n"
            "Relevant due to empirical analysis of CI build failures."
        )
        reasoning, summary = explainer._parse_explanation_response(md_response, 0.72, ["build"])
        assert "Shared focus on CI/CD pipelines" in reasoning
        assert summary == "Relevant due to empirical analysis of CI build failures."

        # Case 2: Unstructured plain prose
        plain_response = "Direct study of build failure prediction in continuous integration."
        reasoning, summary = explainer._parse_explanation_response(plain_response, 0.65, ["build"])
        assert summary == plain_response
        assert "65.00%" in reasoning

    @pytest.mark.asyncio
    async def test_recommendation_service_calls_one_prompt_per_match(self):
        RecommendationService._result_cache.clear()
        service = _create_service_with_mock_db()

        service.embedding_service = MagicMock()
        service.embedding_service.encode_text.return_value = [0.2] * 384

        papers = [
            _make_paper(f"Paper {i}", f"Abstract about software testing {i}")
            for i in range(3)
        ]
        service.repository = MagicMock()
        service.repository.search_by_embedding = AsyncMock(
            return_value=[{"paper": p, "score": 0.8} for p in papers]
        )

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=SimpleNamespace(
                content="<reasoning>Step-by-step rationale.</reasoning><summary>Concise explanation.</summary>"
            )
        )
        service.explanation_service.langchain_explainer.llm = mock_llm
        service.explanation_service.use_langchain = True
        service.explanation_service._llm_failed = False

        response = await service.get_recommendations_for_text(
            text="software testing",
            include_explanations=True,
        )

        assert response.total == 3
        # 3 papers -> exactly 3 LLM calls (1 per paper)
        assert mock_llm.ainvoke.await_count == 3
        assert all(
            rec.explanation.summary == "Concise explanation."
            for rec in response.recommendations
        )
        assert all(
            rec.explanation.reasoning_steps == "Step-by-step rationale."
            for rec in response.recommendations
        )
