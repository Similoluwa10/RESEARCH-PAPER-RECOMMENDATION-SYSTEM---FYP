"""
Sample Papers Seed Data

Populates the database with sample SE research papers for development.
"""

import asyncio
import sys
import os

# Add API path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'apps', 'api'))

from src.models.base import async_session_maker
from src.models.paper import Paper


SAMPLE_PAPERS = [
    {
        "title": "A Deep Learning Approach for Code Clone Detection",
        "abstract": "Code clones are duplicated code fragments that may cause maintenance issues. This paper presents a deep learning-based approach using neural networks to detect semantic code clones that traditional methods miss. Our experiments on BigCloneBench show significant improvement over baseline methods.",
        "authors": ["John Smith", "Jane Doe"],
        "year": 2024,
        "venue": "ICSE",
        "keywords": ["deep learning", "code clone", "neural network", "software maintenance"],
    },
    {
        "title": "Automated Bug Detection Using Graph Neural Networks",
        "abstract": "We propose a graph neural network approach for detecting bugs in source code. By representing code as graphs and learning structural patterns, our method achieves state-of-the-art results on multiple benchmarks. We evaluate our approach on real-world projects.",
        "authors": ["Alice Johnson", "Bob Williams"],
        "year": 2024,
        "venue": "FSE",
        "keywords": ["bug detection", "graph neural network", "static analysis", "machine learning"],
    },
    {
        "title": "An Empirical Study of Code Review Practices in Open Source",
        "abstract": "This paper presents an empirical study of code review practices in large open-source projects. We analyze over 100,000 code reviews from GitHub and identify patterns that correlate with review quality and defect detection rates.",
        "authors": ["Carol Davis", "David Brown"],
        "year": 2023,
        "venue": "MSR",
        "keywords": ["code review", "open source", "empirical study", "software quality"],
    },
    {
        "title": "Transformer-Based Vulnerability Detection in C/C++ Code",
        "abstract": "Security vulnerabilities in C/C++ code remain a critical concern. This paper introduces a transformer-based model for detecting common vulnerability patterns. Our model outperforms existing tools on the SARD and NVD datasets.",
        "authors": ["Eve Martinez", "Frank Garcia"],
        "year": 2024,
        "venue": "ISSTA",
        "keywords": ["vulnerability detection", "transformer", "security", "static analysis"],
    },
    {
        "title": "Refactoring Recommendation Using Code Embeddings",
        "abstract": "We present an approach for recommending refactoring operations using learned code embeddings. Our method identifies code smells and suggests appropriate refactoring patterns based on semantic similarity to known refactoring examples.",
        "authors": ["Grace Lee", "Henry Wilson"],
        "year": 2023,
        "venue": "ASE",
        "keywords": ["refactoring", "code embeddings", "code smell", "software maintenance"],
    },
]


async def seed_papers():
    """Seed the database with sample papers."""
    async with async_session_maker() as session:
        for paper_data in SAMPLE_PAPERS:
            paper = Paper(**paper_data)
            session.add(paper)
        
        await session.commit()
        print(f"Seeded {len(SAMPLE_PAPERS)} sample papers")


if __name__ == "__main__":
    asyncio.run(seed_papers())
