"""
paper_service.py - Paper Service

Business logic for research paper management.
Handles CRUD operations and embedding generation.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.paper import Paper
from src.repositories.paper_repository import PaperRepository
from src.schemas.paper import PaperCreate, PaperListResponse, PaperResponse, PaperUpdate
from src.services.embedding_service import EmbeddingService


class PaperService:
    """
    Service for paper management operations.
    
    Handles business logic and coordinates between
    the router and repository layers.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaperRepository(db)
        self.embedding_service = EmbeddingService()   
    
    async def list_papers(
        self,
        page: int = 1,
        page_size: int = 20,
        year: Optional[int] = None,
        venue: Optional[str] = None,
    ) -> PaperListResponse:
        """
        Get paginated list of papers with optional filters.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            year: Filter by publication year
            venue: Filter by venue/conference
            
        Returns:
            Paginated paper response
        """
        offset = (page - 1) * page_size
        papers = await self.repository.get_all(
            limit=page_size,
            offset=offset,
            year=year,
            venue=venue,
        )
      
        total = await self.repository.count(year=year, venue=venue)
        result = {
            "papers": papers,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        return PaperListResponse.from_model(result)
    
    async def get_paper(self, paper_id: UUID) -> Optional[PaperResponse]:
        """Get a single paper by ID."""
        paper = await self.repository.get_by_id(paper_id)        
        return PaperResponse.from_model(paper) if paper else None
    
    async def create_paper(self, data: PaperCreate) -> PaperResponse:
        """
        Create a new paper and generate its embedding.
        
        Args:
            data: Paper creation data
            
        Returns:
            Created paper response
        """
        paper = await self.repository.create(data.model_dump())
        
        # Generate embedding for the paper
        await self._generate_embedding(paper)        
       
        return PaperResponse.from_model(paper)
    
    async def update_paper(
        self,
        paper_id: UUID,
        data: PaperUpdate,
    ) -> Optional[PaperResponse]:
        """
        Update an existing paper.
        
        Regenerates embedding if title or abstract changed.
        """
        paper = await self.repository.update(paper_id, data.model_dump(exclude_unset=True))
        
        if paper and (data.title or data.abstract):
            # Regenerate embedding if content changed
            await self._generate_embedding(paper)        
        
        return PaperResponse.from_model(paper) if paper else None
    
    async def delete_paper(self, paper_id: UUID) -> bool:
        """Delete a paper by ID."""
        return await self.repository.delete(paper_id)
    
    async def _generate_embedding(self, paper: Paper) -> List[float]:
        """
        Generate embedding vector for paper content.
        
        Combines title and abstract for richer representation.
        Uses packages/nlp embedding module.
        """
        text = self.embedding_service.build_paper_text(paper.title, paper.abstract)
        embedding = self.embedding_service.encode_text(text)
        quality_score = self.embedding_service.compute_quality_score(paper.title, paper.abstract)

        await self.repository.store_embedding(
            paper_id=paper.id,
            vector=embedding,
            model_name=self.embedding_service.model_name,
            model_version="1.0",
            embedding_quality_score=quality_score,
        )

        return embedding
