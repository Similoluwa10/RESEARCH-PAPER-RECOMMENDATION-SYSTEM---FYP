"""
Software Engineering Research Domains

Categories and domains for classifying SE research papers.
"""

# Main SE research areas
SE_DOMAINS = {
    "software_testing": {
        "name": "Software Testing",
        "keywords": ["testing", "test case", "unit test", "integration test", "regression"],
    },
    "software_maintenance": {
        "name": "Software Maintenance",
        "keywords": ["maintenance", "refactoring", "technical debt", "code smell", "legacy"],
    },
    "software_security": {
        "name": "Software Security",
        "keywords": ["security", "vulnerability", "malware", "authentication", "encryption"],
    },
    "machine_learning_se": {
        "name": "Machine Learning for SE",
        "keywords": ["machine learning", "deep learning", "neural network", "AI", "prediction"],
    },
    "code_review": {
        "name": "Code Review",
        "keywords": ["code review", "peer review", "inspection", "quality assurance"],
    },
    "requirements_engineering": {
        "name": "Requirements Engineering",
        "keywords": ["requirements", "specification", "user story", "use case"],
    },
    "software_architecture": {
        "name": "Software Architecture",
        "keywords": ["architecture", "design pattern", "microservices", "monolith"],
    },
    "devops": {
        "name": "DevOps & CI/CD",
        "keywords": ["devops", "continuous integration", "continuous deployment", "docker", "kubernetes"],
    },
    "program_analysis": {
        "name": "Program Analysis",
        "keywords": ["static analysis", "dynamic analysis", "symbolic execution", "program slicing"],
    },
    "software_evolution": {
        "name": "Software Evolution",
        "keywords": ["evolution", "versioning", "changelog", "migration"],
    },
}

# Venues commonly publishing SE research
SE_VENUES = [
    "ICSE",  # International Conference on Software Engineering
    "FSE",   # Foundations of Software Engineering
    "ASE",   # Automated Software Engineering
    "ISSTA", # International Symposium on Software Testing and Analysis
    "MSR",   # Mining Software Repositories
    "ICSME", # International Conference on Software Maintenance and Evolution
    "ESEC",  # European Software Engineering Conference
    "TSE",   # IEEE Transactions on Software Engineering
    "TOSEM", # ACM Transactions on Software Engineering and Methodology
    "EMSE",  # Empirical Software Engineering
    "JSS",   # Journal of Systems and Software
    "IST",   # Information and Software Technology
]


def get_domain_keywords(domain: str) -> list:
    """Get keywords for a specific domain."""
    if domain in SE_DOMAINS:
        return SE_DOMAINS[domain]["keywords"]
    return []


def get_all_keywords() -> list:
    """Get all domain keywords."""
    all_keywords = []
    for domain in SE_DOMAINS.values():
        all_keywords.extend(domain["keywords"])
    return list(set(all_keywords))
