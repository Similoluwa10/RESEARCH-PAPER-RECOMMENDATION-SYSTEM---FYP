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
from src.schemas.paper import PaperCreate, PaperUpdate


class PaperService:
    """
    Service for paper management operations.
    
    Handles business logic and coordinates between
    the router and repository layers.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaperRepository(db)
    
    async def list_papers(
        self,
        page: int = 1,
        page_size: int = 20,
        year: Optional[int] = None,
        venue: Optional[str] = None,
    ) -> Tuple[List[Paper], int]:
        """
        Get paginated list of papers with optional filters.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            year: Filter by publication year
            venue: Filter by venue/conference
            
        Returns:
            Tuple of (papers list, total count)
        """
        offset = (page - 1) * page_size
        papers = await self.repository.get_all(
            limit=page_size,
            offset=offset,
            year=year,
            venue=venue,
        )
        total = await self.repository.count(year=year, venue=venue)
        return papers, total
    
    async def get_paper(self, paper_id: UUID) -> Optional[Paper]:
        """Get a single paper by ID."""
        return await self.repository.get_by_id(paper_id)
    
    async def create_paper(self, data: PaperCreate) -> Paper:
        """
        Create a new paper and generate its embedding.
        
        Args:
            data: Paper creation data
            
        Returns:
            Created paper instance
        """
        paper = await self.repository.create(data.model_dump())
        
        # Generate embedding for the paper
        await self._generate_embedding(paper)
        
        return paper
    
    async def update_paper(
        self,
        paper_id: UUID,
        data: PaperUpdate,
    ) -> Optional[Paper]:
        """
        Update an existing paper.
        
        Regenerates embedding if title or abstract changed.
        """
        paper = await self.repository.update(paper_id, data.model_dump(exclude_unset=True))
        
        if paper and (data.title or data.abstract):
            # Regenerate embedding if content changed
            await self._generate_embedding(paper)
        
        return paper
    
    async def delete_paper(self, paper_id: UUID) -> bool:
        """Delete a paper by ID."""
        return await self.repository.delete(paper_id)
    
    async def _generate_embedding(self, paper: Paper) -> List[float]:
        """
        Generate embedding vector for paper content.
        
        Combines title and abstract for richer representation.
        Uses packages/nlp embedding module.
        """
        # TODO: Implement embedding generation using packages/nlp
        # text = f"{paper.title} {paper.abstract}"
        # embedding = embedding_service.generate(text)
        # await self.repository.store_embedding(paper.id, embedding)
        pass
