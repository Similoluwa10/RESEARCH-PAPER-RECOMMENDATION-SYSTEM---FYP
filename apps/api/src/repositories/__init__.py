"""
Repositories Package

Data access layer.
"""

from src.repositories.base import BaseRepository
from src.repositories.paper_repository import PaperRepository
from src.repositories.user_repository import UserRepository
from src.repositories.interaction_repository import InteractionRepository

__all__ = [
    "BaseRepository",
    "PaperRepository",
    "UserRepository",
    "InteractionRepository",
]
