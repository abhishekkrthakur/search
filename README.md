# Hybrid Search

Vespa + FastAPI demo that now covers both lexical BM25 and dense semantic retrieval with a hybrid (RRF) ranking option.

## Tutorial Series
- Part 1: Set up Vespa search engine, ingest data, and query via curl (https://www.youtube.com/watch?v=lfoOtjLhKh8)
- Part 2: Build an interactive web UI with FastAPI and modern frontend (https://www.youtube.com/watch?v=83k0gnqxE_s)
- Part 3: A no nonsense, applied intro to BM25 (https://www.youtube.com/watch?v=TW9vHU1GpU4)
- Part 4: Hybrid search (lexical + dense) (https://www.youtube.com/watch?v=BXvCxG_H31M)
- Part 5: What is reciprocal rank fusion? (https://youtu.be/2uBcjEecr38)

More coming soon!

Questions or requests? Open a GitHub issue.

## What’s Included
- `bm25.py`: Vespa application package with multiple BM25 rank profiles for lexical experiments.
- `hybrid.py`: Vespa package with BM25 + HNSW vectors and three rank profiles (`bm25`, `semantic`, `fusion` using reciprocal rank fusion).
- `feed.py`: Deploys the hybrid package to a local Vespa Docker container, writes the app to `./vespa_app_hybrid`, encodes documents with `all-MiniLM-L6-v2`, and streams FineWeb into Vespa.
- `ui.py` + `templates/` + `static/`: FastAPI-powered UI that lets you pick ranking modes and handles query embedding for semantic/hybrid searches.

## Prerequisites
- Python 3.10+
- Docker or Podman (for Vespa deployment)
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- Network access to pull HuggingFace FineWeb and the SentenceTransformer model

## Install Dependencies
```bash
uv sync
```

## Deploy Vespa and Ingest Data
This launches a Vespa container with 8 GB memory, writes the Vespa app files to `vespa_app_hybrid/`, and streams FineWeb with on-the-fly embeddings.
```bash
python feed.py
```
Notes:
- Dataset: `HuggingFaceFW/fineweb` split `CC-MAIN-2025-08` (streaming).
- Embeddings: `all-MiniLM-L6-v2` (uses `mps` on Apple Silicon by default).
- Stop with `Ctrl+C` once you have enough documents indexed.

## Query Vespa via curl (BM25)
```bash
curl -X POST http://localhost:8080/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "yql": "select * from sources * where userQuery() limit 10",
    "query": "python programming",
    "ranking": {"profile": "bm25"}
  }'
```

## Run the UI (hybrid/semantic/BM25)
Start the FastAPI server:
```bash
uvicorn ui:app --reload
```
Open http://localhost:8000 and choose a ranking mode:
- `fusion`: hybrid RRF over BM25 + ANN semantic scores
- `semantic`: dense vector only
- `bm25`: lexical only


## Resources
- [Vespa](https://vespa.ai/)
- [pyvespa](https://github.com/vespa-engine/pyvespa)
- [HuggingFace FineWeb](https://huggingface.co/datasets/HuggingFaceFW/fineweb)
- [sentence-transformers](https://www.sbert.net/)
