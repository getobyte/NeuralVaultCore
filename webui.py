#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Web Backend — JSON API + static file server (port 9999)
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from core import get_default_storage as _factory
from core.models import Memory

logging.basicConfig(
    stream=sys.stderr, level=logging.INFO, format="%(asctime)s [NVC-UI] %(message)s"
)
logger = logging.getLogger(__name__)

_storage = None


def _get_storage():
    global _storage
    if _storage is None:
        _storage = _factory()
    return _storage


def _mem_to_dict(mem):
    return mem.to_dict()


def _namespace_from_request(request) -> str:
    return request.query_params.get("ns", "default").strip() or "default"


def _is_disallowed_dist_path(raw_path: str) -> bool:
    if not raw_path:
        return False
    if raw_path.startswith(("/", "\\")) or "\\" in raw_path:
        return True
    if Path(raw_path).drive:
        return True
    return any(part == ".." for part in Path(raw_path).parts)


def _resolve_dist_asset(dist_dir: Path, raw_path: str) -> Path | None:
    if not raw_path:
        return None
    if _is_disallowed_dist_path(raw_path):
        return None

    candidate = (dist_dir / raw_path.lstrip("/")).resolve()
    try:
        candidate.relative_to(dist_dir.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


# ── API Routes ──


async def api_memories_list(request):
    params = request.query_params
    ns = params.get("ns", "")
    limit = int(params.get("limit", "50"))
    offset = int(params.get("offset", "0"))
    memories, total = _get_storage().list_all(ns or None, limit, offset)
    return JSONResponse(
        {
            "memories": [_mem_to_dict(m) for m in memories],
            "total": total,
        }
    )


async def api_memory_detail(request):
    key = request.path_params["key"]
    namespace = _namespace_from_request(request)
    mem = _get_storage().retrieve(key, namespace)
    if not mem:
        return JSONResponse(
            {"error": f"Not found: {key} in namespace {namespace}"}, status_code=404
        )
    return JSONResponse(_mem_to_dict(mem))


async def api_memory_create(request):
    try:
        data = await request.json()
    except Exception as e:
        logger.warning("Invalid JSON for memory create: %s", e)
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    key = data.get("key", "").strip()
    content = data.get("content", "")
    title = data.get("title", "").strip()
    namespace = data.get("namespace", "default").strip()
    tags_raw = data.get("tags", "")
    tags = Memory.parse_tags(tags_raw) if isinstance(tags_raw, str) else tags_raw

    if not key or not content:
        return JSONResponse({"error": "key and content are required"}, status_code=400)

    try:
        mem = _get_storage().store(key, content, tags, title, namespace)
        return JSONResponse(_mem_to_dict(mem), status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def api_memory_delete(request):
    key = request.path_params["key"]
    namespace = _namespace_from_request(request)
    if _get_storage().delete(key, namespace):
        return JSONResponse({"ok": True, "key": key, "namespace": namespace})
    return JSONResponse(
        {"error": f"Not found: {key} in namespace {namespace}"}, status_code=404
    )


async def api_health(request):
    return JSONResponse({"status": "ok", "service": "nvc-webui"})


async def api_stats(request):
    s = _get_storage().get_stats()
    return JSONResponse(
        {
            "total_memories": s.total_memories,
            "total_chars": s.total_chars,
            "namespaces": s.namespaces,
            "db_size_kb": s.db_size_kb,
            "db_path": s.db_path,
        }
    )


async def api_namespaces(request):
    ns = _get_storage().list_namespaces()
    return JSONResponse(ns)


async def api_search(request):
    q = request.query_params.get("q", "")
    ns = request.query_params.get("ns", "")
    if not q:
        return JSONResponse({"memories": [], "total": 0})
    results = _get_storage().search(q, ns or None)
    return JSONResponse(
        {
            "memories": [_mem_to_dict(m) for m in results],
            "total": len(results),
        }
    )


async def api_timeline(request):
    params = request.query_params
    now = datetime.now()
    year = int(params.get("year", str(now.year)))
    month = int(params.get("month", str(now.month)))
    ns = params.get("ns", "")

    storage = _get_storage()
    conn = storage._conn
    prefix = f"{year}-{month:02d}%"

    if ns:
        rows = conn.execute(
            "SELECT key, title, namespace, tags, updated_at FROM memories "
            "WHERE updated_at LIKE ? AND namespace = ? ORDER BY updated_at",
            (prefix, ns),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT key, title, namespace, tags, updated_at FROM memories "
            "WHERE updated_at LIKE ? ORDER BY updated_at",
            (prefix,),
        ).fetchall()

    days: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        key, title, namespace, tags_raw, updated_at = row
        day_key = updated_at[:10]  # YYYY-MM-DD
        tags = [t.strip() for t in (tags_raw or "").split(",") if t.strip()]
        days[day_key].append({
            "key": key,
            "title": title,
            "namespace": namespace,
            "tags": tags,
            "updated_at": updated_at,
        })

    return JSONResponse({"days": dict(days), "total": sum(len(v) for v in days.values())})


async def api_import(request):
    try:
        data = await request.json()
    except Exception as e:
        logger.warning("Invalid JSON for import: %s", e)
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    memories = data.get("memories", [])
    if not isinstance(memories, list):
        return JSONResponse({"error": "memories must be an array"}, status_code=400)

    storage = _get_storage()
    imported = 0
    for mem in memories:
        try:
            key = mem.get("key", "").strip()
            content = mem.get("content", "").strip()
            if not key or not content:
                continue
            tags = mem.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            storage.store(
                key,
                content,
                tags,
                mem.get("title", key),
                mem.get("namespace", "default"),
            )
            imported += 1
        except (ValueError, KeyError) as e:
            logger.warning("Import skipped: %s", e)

    return JSONResponse({"imported": imported, "total": len(memories)})


# ── SPA fallback ──

DIST_DIR = Path(__file__).parent / "webui-dist"


async def spa_fallback(request):
    """Serve index.html for any non-API route (SPA client-side routing)."""
    dist_dir = request.app.state.dist_dir
    asset_path = request.path_params.get("path", "")
    if _is_disallowed_dist_path(asset_path):
        return Response("Not found", status_code=404)
    asset = _resolve_dist_asset(dist_dir, asset_path)
    if asset is not None:
        return FileResponse(str(asset))

    index = dist_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return Response(
        "UI not built. Run: cd 'NVC - BaseUI' && npm run build", status_code=503
    )


# ── App ──


def create_app(dist_dir: Path | None = None) -> Starlette:
    dist_dir = dist_dir or DIST_DIR

    api_routes = [
        Route("/health", api_health),
        Route("/api/memories", api_memories_list, methods=["GET"]),
        Route("/api/memories", api_memory_create, methods=["POST"]),
        Route("/api/memories/{key:path}", api_memory_detail, methods=["GET"]),
        Route("/api/memories/{key:path}", api_memory_delete, methods=["DELETE"]),
        Route("/api/stats", api_stats),
        Route("/api/namespaces", api_namespaces),
        Route("/api/search", api_search),
        Route("/api/timeline", api_timeline),
        Route("/api/import", api_import, methods=["POST"]),
    ]

    routes = list(api_routes)

    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        routes.append(
            Mount("/assets", StaticFiles(directory=str(assets_dir)), name="static")
        )

    routes.append(Route("/{path:path}", spa_fallback))
    routes.append(Route("/", spa_fallback))

    app = Starlette(routes=routes)
    app.state.dist_dir = dist_dir
    _cors_env = os.getenv("NVC_CORS_ORIGINS", "")
    _cors_origins = (
        [o.strip() for o in _cors_env.split(",") if o.strip()]
        if _cors_env
        else [
            "http://localhost:9997",
            "http://127.0.0.1:9997",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="NeuralVaultCore Web Backend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9999)
    args = parser.parse_args()

    logger.info("Starting NVC Backend on http://%s:%d", args.host, args.port)
    if DIST_DIR.exists():
        logger.info("Serving UI from %s", DIST_DIR)
    else:
        logger.info(
            "UI not built — API only. Build: cd 'NVC - BaseUI' && npm run build"
        )
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
