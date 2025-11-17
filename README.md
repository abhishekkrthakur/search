# Simple Search

A lightweight full-text search application powered by Vespa and FastAPI. This project demonstrates building a web-scale search engine from scratch.

## Overview

This is a multi-part tutorial series:

- **Part 1**: Set up Vespa search engine, ingest data, and query via curl (https://www.youtube.com/watch?v=lfoOtjLhKh8)
- **Part 2**: Build an interactive web UI with FastAPI and modern frontend (https://www.youtube.com/watch?v=83k0gnqxE_s)
- More coming soon


## Prerequisites

- Python 3.10 or higher
- Docker or Podman (for Vespa deployment)
- [uv](https://docs.astral.sh/uv/) package manager (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd search
```

2. Install dependencies using uv:
```bash
uv sync
```

## Part 1: Building the Search Backend

### Step 1: Deploy Vespa and Ingest Data

Run [main.py](main.py) to set up the Vespa search engine with a BM25 ranking profile and ingest documents:

```bash
python main.py
```

This script will:
1. Create a Vespa application package with a custom schema
2. Deploy Vespa in a local Docker/Podman container
3. Load documents from the FineWeb dataset
4. Feed documents into Vespa with progress tracking

### Step 2: Test with curl

Once the data is ingested, query the search engine directly:

```bash
curl -X POST http://localhost:8080/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "yql": "select * from sources * where userQuery() limit 10",
    "query": "python programming",
    "ranking": "bm25"
  }'
```

**Query Parameters:**
- `yql`: Vespa Query Language statement
- `query`: Your search terms
- `ranking`: Ranking profile to use (configured as "bm25")

## Part 2: Building the Web UI

### Architecture

The web interface consists of:

- **Backend** ([ui.py](ui.py)): FastAPI application with search endpoint
- **Frontend**: HTML/CSS/JS with modern design
  - [templates/index.html](templates/index.html): Main page structure
  - [static/styles.css](static/styles.css): Dark theme styling with gradients
  - [static/app.js](static/app.js): Search logic and result rendering

### Running the UI

Start the FastAPI server:

```bash
uvicorn ui:app --reload
```

Then open your browser to:
```
http://localhost:8000
```

### Configuration

Environment variables (optional):

```bash
export VESPA_URL="http://localhost"        # Vespa host URL
export VESPA_PORT="8080"                   # Vespa port
export VESPA_RESULT_LIMIT="10"             # Default results per page
export VESPA_MAX_RESULT_LIMIT="100"        # Maximum allowed results
```

## Resources

- [Vespa](https://vespa.ai/) for the search infrastructure
- [HuggingFace FineWeb](https://huggingface.co/datasets/HuggingFaceFW/fineweb) for the dataset
