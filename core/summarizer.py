# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Summarizer — heuristic + optional LLM summarization
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from core.config import NVCConfig
from core.models import Memory
from core.storage import SQLiteStorage

logger = logging.getLogger(__name__)


def _parse_iso(ts: str) -> Optional[datetime]:
    """Parse ISO timestamp, return None on failure."""
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def summarize_heuristic(
    memories: List[Memory],
    since: Optional[datetime] = None,
) -> str:
    """
    Generate a heuristic summary from captured events.
    Groups by namespace and hour, counts command patterns.
    """
    if not memories:
        return "No events to summarize."

    # Filter by time if requested
    if since:
        memories = [
            m for m in memories
            if _parse_iso(m.updated_at) and _parse_iso(m.updated_at) >= since
        ]
        if not memories:
            return f"No events since {since.strftime('%Y-%m-%d %H:%M')}."

    # Group by namespace
    by_namespace: dict = defaultdict(list)
    for m in memories:
        by_namespace[m.namespace].append(m)

    sections = []
    for ns, mems in sorted(by_namespace.items()):
        count = len(mems)

        if ns.startswith("shell:"):
            # Analyze shell commands
            commands = Counter()
            for m in mems:
                first_word = m.content.strip().split()[0] if m.content.strip() else "?"
                first_word = first_word.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                commands[first_word] += 1

            top_cmds = commands.most_common(5)
            cmd_summary = ", ".join(f"{cmd} ({n}x)" for cmd, n in top_cmds)
            sections.append(f"[{ns}] {count} commands — top: {cmd_summary}")

        elif ns.startswith("git:"):
            # Analyze git events
            commits = [m for m in mems if "commit" in m.tags]
            merges = [m for m in mems if "merge" in m.tags]
            checkouts = [m for m in mems if "checkout" in m.tags]

            parts = []
            if commits:
                parts.append(f"{len(commits)} commits")
            if merges:
                parts.append(f"{len(merges)} merges")
            if checkouts:
                branches = set()
                for m in checkouts:
                    for line in m.content.splitlines():
                        if line.startswith("Branch:"):
                            branches.add(line.split(":", 1)[1].strip())
                parts.append(f"{len(checkouts)} branch switches ({', '.join(branches)})")
            sections.append(f"[{ns}] {' | '.join(parts) if parts else f'{count} events'}")

        else:
            sections.append(f"[{ns}] {count} events")

    # Time range
    timestamps = [_parse_iso(m.updated_at) for m in memories if _parse_iso(m.updated_at)]
    if timestamps:
        earliest = min(timestamps).strftime("%H:%M")
        latest = max(timestamps).strftime("%H:%M")
        time_range = f"Time range: {earliest} — {latest}"
    else:
        time_range = ""

    header = f"Summary: {len(memories)} events across {len(by_namespace)} namespace(s)"
    parts = [header]
    if time_range:
        parts.append(time_range)
    parts.extend(sections)
    return "\n".join(parts)


def summarize_llm(
    memories: List[Memory],
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3.2",
) -> Optional[str]:
    """
    Summarize events using a local Ollama LLM.
    Returns None if Ollama is unavailable.
    """
    try:
        import urllib.request
        import json

        # Build context from memories
        events = []
        for m in memories[:50]:  # Limit context
            events.append(f"[{m.namespace}] {m.title}: {m.content[:200]}")
        context = "\n".join(events)

        prompt = (
            "Summarize these developer activity events in 3-5 bullet points. "
            "Focus on what was accomplished, not individual commands. "
            "Keep the total summary under 500 characters:\n\n"
            f"{context}"
        )

        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 256},
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("response", "").strip() or None

    except Exception as e:
        logger.debug("Ollama summarization failed: %s", e)
        return None


def run_summarize(
    storage: SQLiteStorage,
    since_hours: float = 1.0,
    use_llm: bool = False,
) -> str:
    """
    Main entry point: fetch recent events, summarize, store result.
    Returns the summary text.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    # Fetch only shell/git auto-captured memories (filtered at SQL level)
    shell_mems, _ = storage.list_all(namespace_prefix="shell:", limit=500)
    git_mems, _ = storage.list_all(namespace_prefix="git:", limit=500)
    all_mems = shell_mems + git_mems
    recent = [
        m for m in all_mems
        if _parse_iso(m.updated_at) and _parse_iso(m.updated_at) >= since
    ]

    if not recent:
        return f"No captured events in the last {since_hours} hour(s)."

    # Try LLM first if requested
    summary = None
    if use_llm:
        summary = summarize_llm(recent)
        if summary:
            summary = f"(LLM Summary)\n{summary}"

    # Fallback to heuristic
    if not summary:
        summary = summarize_heuristic(recent, since)

    # Store the summary
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    key = f"summary:{now}"
    storage.store(
        key, summary, ["summary", "auto"], f"Activity summary {now}", "summary:daily"
    )

    return summary
