"""FastAPI-powered UI for querying the local Vespa application."""

from __future__ import annotations

import os
import textwrap
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from vespa.application import Vespa


class SearchRequest(BaseModel):
    query: str
    limit: int | None = None
    ranking: str | None = None


RESULT_LIMIT = int(os.getenv("VESPA_RESULT_LIMIT", "10"))
MAX_RESULT_LIMIT = int(os.getenv("VESPA_MAX_RESULT_LIMIT", "100"))
MIN_RESULT_LIMIT = 1
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@lru_cache
def get_vespa_client() -> Vespa:
    """Instantiate (and cache) the Vespa client."""
    url = os.getenv("VESPA_URL", "http://localhost")
    port = int(os.getenv("VESPA_PORT", "8080"))
    return Vespa(url=url, port=port)


def _resolve_limit(candidate: int | None) -> int:
    """Clamp the requested limit to a safe, positive range."""
    limit = candidate if candidate is not None else RESULT_LIMIT
    try:
        limit_value = int(limit)
    except (TypeError, ValueError):
        limit_value = RESULT_LIMIT
    return max(MIN_RESULT_LIMIT, min(MAX_RESULT_LIMIT, limit_value))


def run_vespa_query(query: str, limit: int | None = None, ranking: str | None = None) -> Dict[str, Any]:
    """Execute the Vespa search using the provided query string."""
    effective_limit = _resolve_limit(limit)
    ranking_profile = ranking or "bm25"
    client = get_vespa_client()
    with client.syncio(connections=1) as session:
        response = session.query(
            yql=f"select * from sources * where userQuery() limit {effective_limit}",
            query=query,
            ranking=ranking_profile,
        )

    response_json = _safe_json(response)
    print(response_json)  # Debug output
    root = response_json.get("root", {}) or {}
    hits = getattr(response, "hits", []) or []
    formatted_hits = [_format_hit(hit) for hit in hits]

    total_available = _extract_total_hits(response_json)
    latency_ms = _extract_latency(response_json)

    return {
        "query": query,
        "hits": formatted_hits,
        "returned": len(formatted_hits),
        "limit": effective_limit,
        "total_available": total_available,
        "latency_ms": latency_ms,
        "coverage": root.get("coverage") or {},
        "ranking_profile": ranking_profile,
    }


def _format_hit(hit: Dict[str, Any]) -> Dict[str, Any]:
    fields = hit.get("fields", {})
    text = fields.get("text") or ""
    snippet = " ".join(text.split())
    snippet = textwrap.shorten(snippet, width=360, placeholder="…")
    raw_document_id = fields.get("documentid") or hit.get("id")
    display_document_id = fields.get("id") or _normalize_document_id(raw_document_id)

    return {
        "id": display_document_id,
        "document_id": display_document_id,
        "vespa_document_id": raw_document_id,
        "sddocname": fields.get("sddocname"),
        "source": hit.get("source"),
        "url": fields.get("url"),
        "text": text or None,
        "snippet": snippet,
        "relevance": round(float(hit.get("relevance", 0.0)), 4),
        "fields": fields or {},
    }


def _extract_total_hits(response_json: Dict[str, Any]) -> int:
    root = response_json.get("root", {})
    fields = root.get("fields", {})
    return fields.get("totalCount", len(root.get("children", []) or []))


def _extract_latency(response_json: Dict[str, Any]) -> float:
    timing = response_json.get("timing", {})
    total = timing.get("total") or timing.get("querytime")
    return round(float(total), 3) if total is not None else 0.0


def _safe_json(response: Any) -> Dict[str, Any]:
    for attr in ("json", "get_json"):
        if not hasattr(response, attr):
            continue
        candidate = getattr(response, attr)
        try:
            data = candidate() if callable(candidate) else candidate
        except TypeError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def _normalize_document_id(document_id: Any) -> str | None:
    if not isinstance(document_id, str):
        return None
    if "::" in document_id:
        tail = document_id.rsplit("::", 1)[-1]
        return tail or document_id
    return document_id


app = FastAPI(title="Simple Search UI", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "default_limit": RESULT_LIMIT,
            "max_limit": MAX_RESULT_LIMIT,
        },
    )


@app.post("/search")
async def search(request: SearchRequest) -> Dict[str, Any]:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    try:
        payload = run_vespa_query(query, limit=request.limit, ranking=request.ranking)
    except Exception as exc:  # noqa: BLE001 - surface Vespa issues cleanly
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return payload
