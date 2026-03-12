import enum


class PaperCategory(str, enum.Enum):
    """SE research paper categories — aligned with PaperCategorizer"""
    SOFTWARE_TESTING = "Software Testing"
    SOFTWARE_MAINTENANCE = "Software Maintenance"
    SOFTWARE_SECURITY = "Software Security"
    MACHINE_LEARNING_SE = "Machine Learning for SE"
    CODE_REVIEW = "Code Review"
    REQUIREMENTS_ENGINEERING = "Requirements Engineering"
    SOFTWARE_ARCHITECTURE = "Software Architecture"
    DEVOPS_CICD = "DevOps & CI/CD"
    PROGRAM_ANALYSIS = "Program Analysis"
    SOFTWARE_EVOLUTION = "Software Evolution"
    OTHER = "Other"


class PaperSource(str, enum.Enum):
    """Source of paper data"""
    ARXIV = "arXiv"
    DBLP = "DBLP"
    SEMANTIC_SCHOLAR = "Semantic Scholar"
    DOAJ = "DOAJ"
    ZENODO = "Zenodo"
    MANUAL = "Manual"
    OTHER = "Other"


class UserRole(str, enum.Enum):
    """User roles for authorization"""
    USER = "user"
    ADMIN = "admin"
    RESEARCHER = "researcher"


class InteractionType(str, enum.Enum):
    """Types of user-paper interactions"""
    VIEW = "view"
    BOOKMARK = "bookmark"
    DOWNLOAD = "download"
    CITE = "cite"
    RATE = "rate"
    SHARE = "share"
    COMMENT = "comment"


class ExplanationType(str, enum.Enum):
    """Types of recommendation explanations"""
    SIMILAR_TO_LIKED = "similar_to_liked"
    TRENDING = "trending"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    OTHER = "other"