#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# CLI tool — command-line interface for memory management
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from core.config import NVCConfig
from core.service import MemoryService
from core.storage import SQLiteStorage

logging.basicConfig(
    stream=sys.stderr,
    level=logging.WARNING,
    format="%(levelname)s %(message)s",
)

# ──────────────────────────────────────────────────────────────────────────────
# Lazy storage — initialized once on first use
# ──────────────────────────────────────────────────────────────────────────────

_storage: SQLiteStorage | None = None


def _get_storage() -> SQLiteStorage:
    global _storage
    if _storage is None:
        config = None
        try:
            env_file = Path(__file__).parent / ".env"
            config = NVCConfig.from_env(env_file if env_file.exists() else None)
            _storage = SQLiteStorage(config)
        except Exception as e:
            db_path = config.db_path if config is not None else "<unknown>"
            print(
                f"Error: Could not open database at {db_path}. "
                "Check that the path exists and is writable.",
                file=sys.stderr,
            )
            logging.debug("Storage init error: %s", e)
            sys.exit(1)
    return _storage


# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────


def _print_memory(mem) -> None:
    tags = ", ".join(mem.tags) or "none"
    print(f"┌─ {mem.title}")
    print(f"│  Key:       {mem.key}")
    print(f"│  Namespace: {mem.namespace}")
    print(f"│  Tags:      {tags}")
    print(f"│  Updated:   {mem.updated_at[:16]}")
    print(f"│  Chars:     {mem.chars}")
    print("├─ Content:")
    for line in mem.content.splitlines():
        print(f"│  {line}")
    print("└─")


def _print_list(memories: list) -> None:
    if not memories:
        print("No memories found.")
        return
    print(f"{'KEY':<40} {'NAMESPACE':<16} {'UPDATED':<17} TITLE")
    print("─" * 100)
    for m in memories:
        updated = m.updated_at[:16] if m.updated_at else ""
        title = m.title[:40]
        key = m.key[:39]
        print(f"{key:<40} {m.namespace:<16} {updated:<17} {title}")


# ──────────────────────────────────────────────────────────────────────────────
# Sub-commands
# ──────────────────────────────────────────────────────────────────────────────


def cmd_store(args: argparse.Namespace) -> None:
    content = sys.stdin.read() if args.content == "-" else args.content
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    mem = _get_storage().store(
        args.key, content, tags, args.title or "", args.ns or "default"
    )
    print(f"✅ Stored '{mem.title}' [{mem.namespace}] ({mem.chars} chars)")


def cmd_get(args: argparse.Namespace) -> None:
    mem = _get_storage().retrieve(args.key, args.ns or "default")
    if not mem:
        print(f"❌ Memory not found: '{args.key}' [{args.ns or 'default'}]")
        sys.exit(2)
    _print_memory(mem)


def cmd_search(args: argparse.Namespace) -> None:
    results = _get_storage().search(args.query, args.ns or None)
    if not results:
        print(f"🔍 No results for '{args.query}'")
        return
    print(f"🔍 {len(results)} result(s) for '{args.query}':\n")
    _print_list(results)


def cmd_list(args: argparse.Namespace) -> None:
    limit = args.limit if hasattr(args, "limit") else 50
    offset = args.offset if hasattr(args, "offset") else 0
    memories, total = _get_storage().list_all(args.ns or None, limit, offset)
    if total > 0:
        print(
            f"  Showing {len(memories)}/{total} memories"
            + (f" (offset {offset})" if offset > 0 else "")
        )
    _print_list(memories)


def cmd_delete(args: argparse.Namespace) -> None:
    if not args.yes:
        confirm = input(f"Delete '{args.key}'? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return
    ns = args.ns or "default"
    if _get_storage().delete(args.key, ns):
        print(f"🗑️  Deleted '{args.key}'")
    else:
        print(f"❌ Not found: '{args.key}'")
        sys.exit(2)


def cmd_versions(args: argparse.Namespace) -> None:
    ns = args.ns or "default"
    versions = _get_storage().get_versions(args.key, ns)
    if not versions:
        print(f"No versions for '{args.key}'")
        return
    print(f"📜 Versions for '{args.key}':")
    for v in versions:
        print(f"  v{v.version}  {v.saved_at[:16]}  [{v.namespace}] {v.title}")


def cmd_restore(args: argparse.Namespace) -> None:
    if args.version < 1:
        print("❌ Version must be >= 1", file=sys.stderr)
        sys.exit(1)
    if not args.yes:
        confirm = (
            input(
                f"Restore '{args.key}' to version {args.version}? "
                "Current content will be versioned. [y/N]: "
            )
            .strip()
            .lower()
        )
        if confirm != "y":
            print("Aborted.")
            return
    ns = args.ns or "default"
    mem = _get_storage().restore_version(args.key, ns, args.version)
    if mem:
        print(f"✅ Restored '{args.key}' to version {args.version}")
    else:
        print(f"❌ Version {args.version} not found for '{args.key}'")
        sys.exit(2)


def cmd_namespaces(args: argparse.Namespace) -> None:
    ns_list = _get_storage().list_namespaces()
    if not ns_list:
        print("No namespaces found.")
        return
    for ns in ns_list:
        print(f"  📁 {ns}")


def cmd_export(args: argparse.Namespace) -> None:
    memories = _get_storage().export_all()
    data = []
    for mem in memories:
        data.append(
            {
                "key": mem.key,
                "title": mem.title,
                "content": mem.content,
                "tags": mem.tags,
                "namespace": mem.namespace,
                "created_at": mem.created_at,
                "updated_at": mem.updated_at,
            }
        )
    output = json.dumps(
        {"memories": data, "count": len(data)}, indent=2, ensure_ascii=False
    )
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ Exported {len(data)} memories to '{args.output}'")
    else:
        print(output)


def cmd_import(args: argparse.Namespace) -> None:
    try:
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ Failed to read '{args.input}': {e}")
        sys.exit(1)
    memories = raw.get("memories", raw) if isinstance(raw, dict) else raw
    count = _get_storage().import_all(memories)
    print(f"✅ Imported {count} memories.")


def cmd_stats(args: argparse.Namespace) -> None:
    s = _get_storage().get_stats()
    print("📊 NeuralVaultCore Stats")
    print(f"   Total memories : {s.total_memories}")
    print(f"   Total chars    : {s.total_chars:,}")
    print(f"   Namespaces     : {s.namespaces}")
    print(f"   DB size        : {s.db_size_kb} KB")
    print(f"   DB path        : {s.db_path}")


def cmd_migrate(args: argparse.Namespace) -> None:
    print(f"  Migrating from '{args.json_dir}'...")
    count = MemoryService(_get_storage()).migrate_from_json(args.json_dir)
    print(f"✅ Migrated {count} memories from JSON to SQLite.")


def cmd_install_hooks(args: argparse.Namespace) -> None:
    """Install shell hooks."""
    hooks_dir = Path(__file__).parent / "hooks"

    shell = args.shell
    if not shell:
        # Auto-detect
        import os

        shell_env = os.environ.get("SHELL", "")
        if "zsh" in shell_env:
            shell = "zsh"
        elif "bash" in shell_env:
            shell = "bash"
        elif sys.platform == "win32":
            shell = "powershell"
        else:
            shell = "bash"

    hook_files = {
        "bash": ("bash_hook.sh", "~/.bashrc"),
        "zsh": ("zsh_hook.sh", "~/.zshrc"),
        "powershell": ("powershell_hook.ps1", None),
    }

    if shell not in hook_files:
        print(f"Unknown shell: {shell}. Use: bash, zsh, powershell")
        sys.exit(1)

    hook_file, rc_file = hook_files[shell]
    source = hooks_dir / hook_file

    if not source.exists():
        print(f"Hook file not found: {source}")
        sys.exit(1)

    source_line = f'source "{source}"' if shell != "powershell" else f'. "{source}"'

    if rc_file:
        rc_path = Path(rc_file).expanduser()
        if rc_path.exists():
            content = rc_path.read_text()
            if "NeuralVaultCore" not in content and str(source) not in content:
                with open(rc_path, "a") as f:
                    f.write(f"\n# NeuralVaultCore shell hook\n{source_line}\n")
                print(f"Added hook to {rc_path}")
            else:
                print(f"Hook already in {rc_path}")
        else:
            print(f"RC file not found: {rc_path} — add manually: {source_line}")
    else:
        profile_path = (
            "$PROFILE"
            if sys.platform == "win32"
            else "~/.config/powershell/Microsoft.PowerShell_profile.ps1"
        )
        print(f"Add to your PowerShell profile ({profile_path}):")
        print(f"  {source_line}")

    print("Done.")


def cmd_uninstall_hooks(args: argparse.Namespace) -> None:
    """Remove NVC hook lines from shell RC files."""
    rc_files = [
        Path("~/.bashrc").expanduser(),
        Path("~/.zshrc").expanduser(),
    ]
    for rc in rc_files:
        if not rc.exists():
            continue
        lines = rc.read_text().splitlines()
        new_lines = [
            line
            for line in lines
            if "NeuralVaultCore" not in line
            and "shell_capture" not in line
            and "nvc_capture" not in line
            and "nvc_preexec" not in line
            and "nvc_precmd" not in line
            and "hooks/bash_hook" not in line
            and "hooks/zsh_hook" not in line
        ]
        if len(new_lines) < len(lines):
            rc.write_text("\n".join(new_lines) + "\n")
            print(f"Cleaned {rc}")
    print("For PowerShell: remove the source line from $PROFILE manually.")


def cmd_summarize(args: argparse.Namespace) -> None:
    """Generate activity summary."""
    from core.summarizer import run_summarize

    storage = _get_storage()
    summary = run_summarize(storage, args.hours, use_llm=args.llm)
    print(summary)


def cmd_watch(args: argparse.Namespace) -> None:
    """Watch a directory for file changes."""
    from core.watcher import watch_directory

    storage = _get_storage()
    ns = args.ns or f"watch:{Path(args.path).name}"
    print(f"Watching {args.path} (namespace: {ns}) — Ctrl+C to stop")
    watch_directory(args.path, storage, ns)


def cmd_setup_model(args: argparse.Namespace) -> None:
    """Download and cache the semantic search model."""
    print("Downloading semantic search model (all-MiniLM-L6-v2, ~80MB)...")
    try:
        from sentence_transformers import SentenceTransformer

        SentenceTransformer("all-MiniLM-L6-v2")
        print("Model ready. Semantic search is now active.")
    except ImportError:
        print(
            "sentence-transformers not installed. Run: pip install sentence-transformers"
        )
        sys.exit(1)
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)


def cmd_serve(args: argparse.Namespace) -> None:
    """Start MCP server."""
    import subprocess

    cmd = [sys.executable, str(Path(__file__).parent / "server.py")]
    if args.transport:
        cmd.extend(["--transport", args.transport])
    if args.host:
        cmd.extend(["--host", args.host])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.no_auth:
        cmd.append("--no-auth")
    try:
        result = subprocess.run(cmd)
    except KeyboardInterrupt:
        pass
    else:
        sys.exit(result.returncode)


def cmd_print_config(args: argparse.Namespace) -> None:
    """Generate MCP client config snippets."""
    env_file = Path(__file__).parent / ".env"
    config = NVCConfig.from_env(env_file if env_file.exists() else None)

    server_py = str(Path(__file__).parent.resolve() / "server.py")
    python = sys.executable

    base_url = args.base_url or f"http://{config.mcp_host}:{config.mcp_port}"

    snippets = {
        "claude-code": {
            "stdio": f'{{"mcpServers": {{"neural-vault-core": {{"command": "{python}", "args": ["{server_py}"]}}}}}}',
            "sse": f'{{"mcpServers": {{"neural-vault-core": {{"url": "{base_url}/sse", "headers": {{"Authorization": "Bearer {config.api_key or "YOUR_KEY"}"}}}}}}}}',
        },
        "cursor": {
            "stdio": f'{{"mcpServers": {{"neural-vault-core": {{"command": "{python}", "args": ["{server_py}"]}}}}}}',
            "sse": f'{{"mcpServers": {{"neural-vault-core": {{"url": "{base_url}/sse", "headers": {{"Authorization": "Bearer {config.api_key or "YOUR_KEY"}"}}}}}}}}',
        },
    }

    client = args.client or "claude-code"
    transport = config.transport

    if client in snippets and transport in snippets[client]:
        print(f"# {client} ({transport}) config:")
        print(snippets[client][transport])
    else:
        # Generic
        print(f"# MCP config for {client}:")
        if transport == "stdio":
            print(
                f'{{"mcpServers": {{"neural-vault-core": {{"command": "{python}", "args": ["{server_py}"]}}}}}}'
            )
        else:
            print(
                f'{{"mcpServers": {{"neural-vault-core": {{"url": "{base_url}/sse"}}}}}}'
            )


def cmd_init(args: argparse.Namespace) -> None:
    """First-time setup wizard."""
    from install import main as install_main

    install_main()


def cmd_doctor(args: argparse.Namespace) -> None:
    """Run diagnostic checks."""
    from core.doctor import run_doctor

    env_file = Path(__file__).parent / ".env"
    config = NVCConfig.from_env(env_file if env_file.exists() else None)
    results = run_doctor(config)
    for status, cat, msg in results:
        icon = {"OK": "+", "WARN": "!", "ERROR": "-"}.get(status, "?")
        print(f"  [{icon}] [{cat}] {msg}")
    errors = sum(1 for s, _, _ in results if s == "ERROR")
    if errors:
        print(f"\n  {errors} error(s) found.")
        sys.exit(1)
    print("\n  All checks passed.")


def cmd_repair(args: argparse.Namespace) -> None:
    """Run maintenance and optimization."""
    from core.repair import run_repair

    storage = _get_storage()
    results = run_repair(storage)
    for status, msg in results:
        icon = {"OK": "+", "WARN": "!", "ERROR": "-", "SKIP": "~"}.get(status, "?")
        print(f"  [{icon}] {msg}")


def cmd_checkpoint(args: argparse.Namespace) -> None:
    """Update _state for a namespace."""
    storage = _get_storage()
    content = args.content
    if content == "-":
        content = sys.stdin.read()

    if len(content) > 500:
        print(
            f"  Warning: _state is {len(content)} chars (recommended max: 500)",
            file=sys.stderr,
        )

    storage.store(
        "_state",
        content,
        ["state", "checkpoint"],
        f"_state for {args.namespace}",
        args.namespace,
    )
    print(f"  Checkpoint updated: {args.namespace}/_state ({len(content)} chars)")


def cmd_dashboard(args: argparse.Namespace) -> None:
    """Start web dashboard."""
    from webui import main as dashboard_main

    sys.argv = ["webui", "--host", args.host, "--port", str(args.port)]
    dashboard_main()


def cmd_daemon(args: argparse.Namespace) -> None:
    """Manage NVC daemon."""
    from core.daemon import start, stop, status

    if args.action == "start":
        watch_paths = args.watch or []
        pid = start(watch_paths, args.interval)
        print(f"Daemon started (PID {pid})")
    elif args.action == "stop":
        if stop():
            print("Daemon stopped.")
        else:
            sys.exit(1)
    elif args.action == "status":
        st = status()
        if st["running"]:
            print(f"Daemon running (PID {st['pid']})")
            if "watch_paths" in st:
                print(f"  Watch paths: {st['watch_paths']}")
            if "started_at" in st:
                print(f"  Started: {st['started_at']}")
        else:
            print("Daemon is not running.")


def cmd_import_from(args: argparse.Namespace) -> None:
    """Import memories from various sources."""
    from core.importers import (
        import_markdown_files,
        import_obsidian_vault,
        import_notion_export,
        import_plain_text,
        import_json_file,
    )

    source_type = args.source_type
    path = args.path
    ns = args.ns

    importers = {
        "markdown": lambda: import_markdown_files(path, ns or "imported:markdown"),
        "obsidian": lambda: import_obsidian_vault(path, ns or "imported:obsidian"),
        "notion": lambda: import_notion_export(path, ns or "imported:notion"),
        "text": lambda: import_plain_text(path, ns or "imported:text"),
        "json": lambda: import_json_file(path, ns or "imported:json"),
    }

    if source_type not in importers:
        print(f"Unknown source type: {source_type}")
        sys.exit(1)

    try:
        memories = importers[source_type]()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not memories:
        print("No memories found to import.")
        return

    storage = _get_storage()
    count = 0
    for mem in memories:
        try:
            tags = mem.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            storage.store(
                mem["key"],
                mem["content"],
                tags,
                mem.get("title", mem["key"]),
                mem.get("namespace", "default"),
            )
            count += 1
        except Exception as e:
            print(f"  Skipped {mem.get('key', '?')}: {e}", file=sys.stderr)

    print(f"Imported {count}/{len(memories)} memories from {source_type} source.")


def cmd_backup(args: argparse.Namespace) -> None:
    """Create a backup of the database."""
    from datetime import datetime

    storage = _get_storage()
    db_path = Path(storage.db_path)

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)

    if args.output:
        backup_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.parent / f"nvc_backup_{timestamp}.db"

    storage.backup_to(backup_path)

    size_kb = round(backup_path.stat().st_size / 1024, 1)
    print(f"Backup created: {backup_path} ({size_kb} KB)")


def cmd_restore_backup(args: argparse.Namespace) -> None:
    """Restore database from a backup file."""
    import shutil

    backup_path = Path(args.backup_file)
    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}")
        sys.exit(1)

    storage = _get_storage()
    db_path = Path(storage.db_path)

    if not args.yes:
        confirm = (
            input(
                f"Restore from '{backup_path}'? This will REPLACE the current database. [y/N]: "
            )
            .strip()
            .lower()
        )
        if confirm != "y":
            print("Aborted.")
            return

    # Create a safety backup of current DB first
    if db_path.exists():
        safety = db_path.parent / f"{db_path.stem}_before_restore{db_path.suffix}"
        shutil.copy2(str(db_path), str(safety))
        print(f"Safety backup of current DB: {safety}")

    # Close current connection and copy
    storage.restore_from(backup_path)

    # Re-init storage
    global _storage
    _storage = None

    stats = _get_storage().get_stats()
    print(
        f"Restored from {backup_path}: {stats.total_memories} memories, {stats.db_size_kb} KB"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Argument parser
# ──────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nvc",
        description="NeuralVaultCore v1.0 — local AI memory vault",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("store", help="Store a memory")
    p.add_argument("key")
    p.add_argument("content", help="Content or '-' for stdin")
    p.add_argument("--tags", default="")
    p.add_argument("--title", default="")
    p.add_argument("--ns", default="default")
    p.set_defaults(func=cmd_store)

    p = sub.add_parser("get", help="Retrieve a memory by key")
    p.add_argument("key")
    p.add_argument("--ns", default="default")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("search", help="Search memories (FTS5)")
    p.add_argument("query")
    p.add_argument("--ns", default="")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("list", help="List all memories")
    p.add_argument("--ns", default="")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--offset", type=int, default=0)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("delete", help="Delete a memory")
    p.add_argument("key")
    p.add_argument("--ns", default="")
    p.add_argument("-y", "--yes", action="store_true")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("versions", help="List versions of a memory")
    p.add_argument("key")
    p.add_argument("--ns", default="")
    p.set_defaults(func=cmd_versions)

    p = sub.add_parser("restore", help="Restore a previous version")
    p.add_argument("key")
    p.add_argument("version", type=int)
    p.add_argument("--ns", default="")
    p.add_argument("-y", "--yes", action="store_true")
    p.set_defaults(func=cmd_restore)

    p = sub.add_parser("namespaces", help="List all namespaces")
    p.set_defaults(func=cmd_namespaces)

    p = sub.add_parser("export", help="Export memories to JSON")
    p.add_argument("output", nargs="?", help="Output file (default: stdout)")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("import", help="Import memories from JSON")
    p.add_argument("input")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("stats", help="Storage statistics")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("migrate", help="Migrate from ContextKeep JSON")
    p.add_argument("json_dir", help="Directory with old JSON files")
    p.set_defaults(func=cmd_migrate)

    # Hooks
    p = sub.add_parser("install-hooks", help="Install shell hooks")
    p.add_argument("--shell", choices=["bash", "zsh", "powershell"], default=None)
    p.set_defaults(func=cmd_install_hooks)

    p = sub.add_parser("uninstall-hooks", help="Remove NVC hooks")
    p.set_defaults(func=cmd_uninstall_hooks)

    # Summarize
    p = sub.add_parser("summarize", help="Generate activity summary")
    p.add_argument("--hours", type=float, default=1.0, help="Hours to look back")
    p.add_argument("--llm", action="store_true", help="Use Ollama LLM for summary")
    p.set_defaults(func=cmd_summarize)

    # Watch
    p = sub.add_parser("watch", help="Watch directory for changes")
    p.add_argument("path", help="Directory to watch")
    p.add_argument("--ns", default="", help="Namespace (default: watch:<dirname>)")
    p.set_defaults(func=cmd_watch)

    # Daemon
    p = sub.add_parser("daemon", help="Manage NVC daemon")
    p.add_argument("action", choices=["start", "stop", "status"])
    p.add_argument("--watch", nargs="*", help="Directories to watch")
    p.add_argument(
        "--interval", type=float, default=1.0, help="Summary interval (hours)"
    )
    p.set_defaults(func=cmd_daemon)

    # Dashboard
    p = sub.add_parser("setup-model", help="Download semantic search model")
    p.set_defaults(func=cmd_setup_model)

    p = sub.add_parser("dashboard", help="Start web dashboard")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=9999)
    p.set_defaults(func=cmd_dashboard)

    # Backup / Restore
    p = sub.add_parser("backup", help="Backup the database")
    p.add_argument(
        "output", nargs="?", help="Output file path (default: auto-named in data/)"
    )
    p.set_defaults(func=cmd_backup)

    p = sub.add_parser("restore-backup", help="Restore database from backup")
    p.add_argument("backup_file", help="Path to backup .db file")
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    p.set_defaults(func=cmd_restore_backup)

    # Import from external sources
    p = sub.add_parser(
        "import-from", help="Import from Notion/Obsidian/markdown/text/json"
    )
    p.add_argument(
        "source_type", choices=["markdown", "obsidian", "notion", "text", "json"]
    )
    p.add_argument("path", help="File or directory path")
    p.add_argument("--ns", default="", help="Override namespace")
    p.set_defaults(func=cmd_import_from)

    # F4 — Transport
    p = sub.add_parser("serve", help="Start MCP server")
    p.add_argument("--transport", choices=["stdio", "sse"])
    p.add_argument("--host")
    p.add_argument("--port", type=int)
    p.add_argument("--no-auth", action="store_true")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("print-config", help="Generate MCP client config")
    p.add_argument("--client", choices=["claude-code", "cursor", "vscode", "opencode"])
    p.add_argument("--base-url", help="Override base URL for remote")
    p.set_defaults(func=cmd_print_config)

    # F5 — Ops CLI
    p = sub.add_parser("init", help="First-time setup wizard")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("doctor", help="Run diagnostic checks")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("repair", help="Run maintenance and optimization")
    p.set_defaults(func=cmd_repair)

    p = sub.add_parser("checkpoint", help="Update _state for a namespace")
    p.add_argument("namespace")
    p.add_argument("content", help="State content or '-' for stdin")
    p.set_defaults(func=cmd_checkpoint)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        logging.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
