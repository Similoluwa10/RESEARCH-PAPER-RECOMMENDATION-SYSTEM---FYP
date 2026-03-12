import enum


class PaperCategory(str, enum.Enum):
    """SE research paper categories"""
    SOFTWARE_TESTING = "Software Testing"
    AGILE_DEVOPS = "Agile/DevOps"
    REQUIREMENTS_ENGINEERING = "Requirements Engineering"
    SOFTWARE_ARCHITECTURE = "Software Architecture"
    PROGRAM_ANALYSIS = "Program Analysis"
    CODE_QUALITY = "Code Quality"
    OTHER = "Other"


class PaperSource(str, enum.Enum):
    """Source of paper data"""
    ARXIV = "arXiv"
    DBLP = "DBLP"
    SEMANTIC_SCHOLAR = "Semantic Scholar"
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