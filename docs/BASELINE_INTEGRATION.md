# TF-IDF Baseline Integration

This document describes the TF-IDF baseline implementation for evaluating semantic search performance.

## Overview

A TF-IDF + Cosine Similarity baseline has been integrated into the project for comparative evaluation. This allows you to compare:
- **Semantic Search**: Uses sentence-transformer embeddings and pgvector for vector similarity
- **TF-IDF Search**: Traditional bag-of-words TF-IDF vectorization with cosine similarity
- **Hybrid Search**: Combines both methods with configurable weighting

## Architecture

### Components

1. **BaselineService** (`apps/api/src/services/baseline_service.py`)
   - Manages TF-IDF model initialization and fitting
   - Provides search functionality with optional filtering
   - Offers comparison utilities to evaluate both methods
   - Status tracking and refitting capabilities

2. **Enhanced SearchService** (`apps/api/src/services/search_service.py`)
   - Integrates BaselineService for keyword search
   - Routes requests to appropriate search method
   - Unified interface across all search methods

3. **Search Router** (`apps/api/src/routers/search.py`)
   - **POST `/search`** - Full search with configurable method
   - **POST `/search/semantic`** - Semantic search only
   - **POST `/search/keyword`** - TF-IDF keyword search
   - **POST `/search/compare`** - Side-by-side comparison of methods
   - **GET `/search/baseline/status`** - Check baseline initialization status
   - **POST `/search/baseline/initialize`** - Initialize/refit baseline model

## Usage

### 1. Initialize the Baseline Model

The TF-IDF model needs to be initialized before use. This loads all papers and builds the vectorizer.

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/search/baseline/initialize
```

**Via Script:**
```python
from src.services.baseline_service import BaselineService

async with AsyncSession(engine) as session:
    baseline = BaselineService(session)
    await baseline.initialize()
```

### 2. Perform Searches

#### Semantic Search
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning in software testing",
    "top_k": 10,
    "method": "semantic"
  }'
```

#### Keyword (TF-IDF) Search
```bash
curl -X POST http://localhost:8000/api/v1/search/keyword \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning in software testing",
    "top_k": 10
  }'
```

#### Compare Both Methods
```bash
curl -X POST http://localhost:8000/api/v1/search/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning in software testing",
    "top_k": 10
  }'
```

Response includes:
- Results from both methods
- Overlap analysis (papers found by both, only semantic, only TF-IDF)
- Overlap percentage at k

### 3. Run Benchmarks

Execute the comprehensive benchmark suite to evaluate performance across multiple queries:

```bash
python scripts/benchmark_baseline.py
```

This will:
- Run 10 sample queries
- Compare semantic vs TF-IDF results
- Calculate overlap and score metrics
- Save detailed results to `benchmark_results/`

Customize test queries by editing the `test_queries` list in the script.

## Configuration

### TF-IDF Vectorizer Parameters

Edit `BaselineService.__init__()` to customize:

```python
self.tfidf_model = TFIDFBaseline(
    max_features=10000,          # Vocabulary size
    ngram_range=(1, 2),          # Unigrams and bigrams
    min_df=2,                    # Minimum document frequency
    max_df=0.95,                 # Maximum document frequency
)
```

Refer to [scikit-learn TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) for parameter details.

### YAML Configuration

A baseline configuration file exists at `experiments/configs/baseline_tfidf.yaml`:

```yaml
vectorizer:
  max_features: 10000
  ngram_range: [1, 2]
  min_df: 2
  max_df: 0.95
  stop_words: "english"

search:
  top_k: 10
  similarity_metric: "cosine"
```

## API Response Format

### Comparison Response
```json
{
  "query": "machine learning in software testing",
  "semantic": {
    "method": "semantic",
    "total": 10,
    "paper_ids": ["id1", "id2", ...],
    "scores": [0.89, 0.85, ...]
  },
  "tfidf": {
    "method": "tfidf",
    "total": 10,
    "paper_ids": ["id1", "id3", ...],
    "scores": [0.72, 0.68, ...]
  },
  "comparison": {
    "overlap_at_k": 8,
    "overlap_percentage": 80.0,
    "only_in_semantic": ["id4", "id5"],
    "only_in_tfidf": ["id6"]
  }
}
```

## Metrics and Evaluation

### Overlap Analysis
- **Overlap Count**: Number of papers appearing in both result sets
- **Overlap Percentage**: (overlap_count / top_k) × 100
- **Unique to Method**: Papers retrieved only by one method

### Score Metrics
- **Average Score**: Mean relevance score across top-k results
- **Score Distribution**: Used to compare ranking quality

### Suggested Evaluation Metrics

For detailed evaluation, implement:
- **Precision@k**: Fraction of retrieved documents that are relevant
- **Recall@k**: Fraction of relevant documents that are retrieved
- **MAP (Mean Average Precision)**: Position-aware ranking metric
- **NDCG (Normalized Discounted Cumulative Gain)**: Ranking quality metric

Reference: `experiments/evaluation/metrics.py`

## Integration with Experiments

The existing benchmark framework (`experiments/evaluation/benchmark.py`) uses the same `TFIDFBaseline` class:

```python
from src.baselines import TFIDFBaseline

# In experiments
tfidf = TFIDFBaseline()
tfidf.fit(corpus)
results = tfidf.search(query, top_k=10)
```

Results are compatible with existing evaluation metrics.

## Performance Notes

- **First Search**: May be slower due to model initialization if not pre-fitted
- **Memory Usage**: TF-IDF vectorizer holds document vectors in memory (scales with corpus size)
- **For 17,910 Papers**: Expect ~1-2 MB for TF-IDF sparse matrix with 10K features
- **Query Speed**: ~1-5ms per query on modern hardware

## Refitting the Model

When new papers are added to the database:

```python
baseline = BaselineService(session)
await baseline.refit()
```

Or via API:
```bash
curl -X POST http://localhost:8000/api/v1/search/baseline/initialize
```

## Troubleshooting

### Model Not Initialized
Error: "TF-IDF model not initialized"

**Solution**: Initialize via API endpoint or `await baseline.initialize()`

### Memory Issues with Large Corpus
**Solution**: Reduce `max_features` in TFIDFBaseline initialization

### Slow Initialization
- First initialization loads all papers from database
- Subsequent searches use cached model
- Consider running initialization during off-peak hours

## Next Steps

1. **Run Benchmark**: Execute `python scripts/benchmark_baseline.py`
2. **Evaluate Results**: Analyze overlap and score distributions
3. **Tune Parameters**: Adjust TF-IDF configuration for your domain
4. **Implement Metrics**: Add precision, recall, MAP, NDCG calculations
5. **Compare with Semantic**: Use comparison endpoint for side-by-side evaluation

## References

- [TF-IDF](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)
- [Scikit-learn TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [Information Retrieval Metrics](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval))
