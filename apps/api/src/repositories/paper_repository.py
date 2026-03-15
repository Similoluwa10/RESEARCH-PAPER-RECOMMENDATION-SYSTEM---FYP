"""
paper_repository.py - Paper Repository

Data access layer for Paper entities.
Handles all database operations for research papers.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.embedding import Embedding
from src.models.paper import Paper
from src.repositories.base import BaseRepository


class PaperRepository(BaseRepository[Paper]):
    """
    Repository for Paper entities.
    
    Provides CRUD operations and specialized queries
    for research papers, including vector similarity search.
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Paper)
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        year: Optional[int] = None,
        venue: Optional[str] = None,
    ) -> List[Paper]:
        """Get papers with optional filtering."""
        query = select(Paper)
        
        # Apply filters
        conditions = []
        if year:
            conditions.append(Paper.year == year)
        if venue:
            conditions.append(Paper.venue.ilike(f"%{venue}%"))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.limit(limit).offset(offset).order_by(Paper.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        year: Optional[int] = None,
        venue: Optional[str] = None,
    ) -> int:
        """Count papers with optional filtering."""
        query = select(func.count()).select_from(Paper)
        
        conditions = []
        if year:
            conditions.append(Paper.year == year)
        if venue:
            conditions.append(Paper.venue.ilike(f"%{venue}%"))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def find_by_venue(
        self,
        venue: str,
        limit: int = 100,
    ) -> List[Paper]:
        """Find papers by conference/journal venue."""
        result = await self.db.execute(
            select(Paper)
            .where(Paper.venue.ilike(f"%{venue}%"))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def find_by_year(
        self,
        year: int,
        limit: int = 100,
    ) -> List[Paper]:
        """Find papers by publication year."""
        result = await self.db.execute(
            select(Paper).where(Paper.year == year).limit(limit)
        )
        return list(result.scalars().all())
    
    #this is the function which implements sematic search
    async def find_similar(
        self,
        paper_id: UUID,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Find similar papers using vector similarity.
        
        Uses pgvector for efficient cosine similarity search.
        """
        source_result = await self.db.execute(
            select(Embedding).where(Embedding.paper_id == paper_id)
        )
        source_embedding = source_result.scalar_one_or_none()
        if source_embedding is None:
            return []

        return await self.search_by_embedding(
            embedding=source_embedding.vector,
            top_k=top_k,
            exclude_paper_id=paper_id,
        )
    
    async def search_by_embedding(
        self,
        embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        exclude_paper_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search papers by embedding similarity.
        
        Uses pgvector's cosine distance operator (<=>).
        """
        distance = Embedding.vector.cosine_distance(embedding)
        similarity = (1 - distance).label("similarity")

        query = (
            select(Paper, similarity)
            .join(Embedding, Embedding.paper_id == Paper.id)
        )

        conditions = []
        if exclude_paper_id is not None:
            conditions.append(Paper.id != exclude_paper_id)

        if filters:
            year_min = filters.get("year_min")
            year_max = filters.get("year_max")
            venues = filters.get("venues") or []
            keywords = filters.get("keywords") or []

            if year_min is not None:
                conditions.append(Paper.year >= year_min)
            if year_max is not None:
                conditions.append(Paper.year <= year_max)
            if venues:
                conditions.append(or_(*[Paper.venue.ilike(f"%{venue}%") for venue in venues]))
            if keywords:
                conditions.append(Paper.keywords.overlap(keywords))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(distance).limit(top_k)
        rows = (await self.db.execute(query)).all()

        results: List[Dict[str, Any]] = []
        for paper, score in rows:
            bounded_score = max(0.0, min(1.0, float(score)))
            results.append({"paper": paper, "score": bounded_score})

        return results
    
    async def store_embedding(
        self,
        paper_id: UUID,
        vector: List[float],
        model_name: str,
        model_version: str = "1.0",
        embedding_quality_score: Optional[float] = None,
    ) -> Embedding:
        """
        Store or update paper embedding.
        
        Args:
            paper_id: ID of the paper
            vector: Embedding vector
            model_name: Name of the embedding model used
            
        Returns:
            Created or updated Embedding instance
        """
        # Check if embedding exists
        result = await self.db.execute(
            select(Embedding).where(Embedding.paper_id == paper_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.vector = vector
            existing.model_name = model_name
            existing.model_version = model_version
            existing.embedding_quality_score = embedding_quality_score
            await self.db.commit()
            return existing
        
        # Create new embedding
        embedding = Embedding(
            paper_id=paper_id,
            vector=vector,
            model_name=model_name,
            model_version=model_version,
            embedding_quality_score=embedding_quality_score,
        )
        self.db.add(embedding)
        await self.db.commit()
        await self.db.refresh(embedding)
        return embedding
