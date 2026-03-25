#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Installer wizard — venv, deps, .env, DB init, MCP config
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import json
import os
import platform
import secrets
import subprocess
import sys
from pathlib import Path

BANNER = r"""
 ═══════════════════════════════════════════════════════════════════════════
   ██████╗██╗   ██╗██████╗ ███████╗██████╗       ██████╗ ██████╗  █████╗
  ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗      ██╔══██╗██╔══██╗██╔══██╗
  ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝█████╗██║  ██║██████╔╝███████║
  ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗╚════╝██║  ██║██╔══██╗██╔══██║
  ╚██████╗   ██║   ██████╔╝███████╗██║  ██║      ██████╔╝██║  ██║██║  ██║
   ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

             NeuralVaultCore v1.0 — Infinite Long-Term Memory
                   Cyber-Draco Legacy  |  by getobyte
 ═══════════════════════════════════════════════════════════════════════════
"""

SEP = "─" * 60


def step(msg: str) -> None:
    print(f"  [+] {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    print(f"  [!] {msg}", file=sys.stderr)


def err(msg: str) -> None:
    print(f"  [-] ERROR: {msg}", file=sys.stderr)


def check_python() -> None:
    step(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")
    if sys.version_info < (3, 10):
        err("Python 3.10+ required.")
        sys.exit(1)


def create_venv() -> Path:
    venv = Path("venv")
    if venv.exists():
        step("Virtual environment already exists — skipping")
    else:
        step("Creating virtual environment...")
        subprocess.check_call(
            [sys.executable, "-m", "venv", "venv"],
            stdout=subprocess.DEVNULL,
        )
        step("Virtual environment created")

    if platform.system() == "Windows":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def install_deps(python: Path) -> None:
    step("Upgrading pip...")
    subprocess.check_call(
        [str(python), "-m", "pip", "install", "--upgrade", "pip", "-q"],
    )
    step("Installing dependencies...")
    subprocess.check_call(
        [str(python), "-m", "pip", "install", "-e", ".[full]", "-q"],
    )
    step("Dependencies installed")

    # Pre-download semantic search model
    step("Downloading semantic search model (all-MiniLM-L6-v2, ~80MB)...")
    result = subprocess.run(
        [
            str(python),
            "-c",
            "from sentence_transformers import SentenceTransformer; "
            "SentenceTransformer('all-MiniLM-L6-v2'); "
            "print('Model ready')",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        step("Semantic search model downloaded")
    else:
        warn("Model download failed (semantic search will use FTS5 fallback)")


def generate_env(profile: str = "local-ui") -> dict[str, str]:
    env_path = Path(".env")
    if env_path.exists():
        warn(".env already exists — keeping existing config")
        config: dict[str, str] = {}
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                config[k.strip()] = v.strip()
        return config

    api_key = "nvc_" + secrets.token_hex(24)
    nvc_home = str(Path(__file__).parent.resolve())

    config = {
        "NVC_API_KEY": api_key,
        "NVC_DB_PATH": str(Path(nvc_home) / "data" / "nvc.db"),
        "NVC_MCP_PORT": "9998",
        "NVC_PROFILE": profile,
    }

    lines = [
        "# NeuralVaultCore v1.0 — Configuration",
        "# Generated automatically. DO NOT commit this file.",
        "",
    ] + [f"{k}={v}" for k, v in config.items()]

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    step(".env generated")
    return config


def init_db(python: Path) -> None:
    step("Initializing SQLite database...")
    result = subprocess.run(
        [
            str(python),
            "-c",
            "import sys; sys.path.insert(0,'.')\n"
            "from core.config import NVCConfig\n"
            "from core.storage import SQLiteStorage\n"
            "from pathlib import Path\n"
            "cfg = NVCConfig.from_env(Path('.env'))\n"
            "s = SQLiteStorage(cfg)\n"
            "print(s.get_stats().db_path)",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err(f"DB init failed: {result.stderr.strip()}")
        sys.exit(1)
    step(f"Database ready: {result.stdout.strip()}")


def generate_mcp_config(python: Path) -> None:
    config = {
        "mcpServers": {
            "neural-vault-core": {
                "command": str(python.resolve()),
                "args": [str(Path("server.py").resolve())],
            }
        }
    }
    Path("mcp_config.json").write_text(
        json.dumps(config, indent=2),
        encoding="utf-8",
    )
    step("mcp_config.json generated")


def install_cli(python: Path) -> None:
    nvc_script = Path("nvc.py").resolve()
    if platform.system() == "Windows":
        bat = python.parent / "nvc.bat"
        bat.write_text(
            f'@echo off\n"{python.resolve()}" "{nvc_script}" %*\n',
            encoding="utf-8",
        )
        step(f"CLI wrapper: {bat}")
        warn(f"Add to PATH: {python.parent}")
    else:
        wrapper = python.parent / "nvc"
        wrapper.write_text(
            f'#!/bin/sh\nexec "{python.resolve()}" "{nvc_script}" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        step(f"CLI wrapper: {wrapper}")
        warn(f"Or run: sudo ln -s {wrapper} /usr/local/bin/nvc")


def build_webui() -> None:
    """Build React frontend if Node.js is available."""
    ui_dir = Path(__file__).parent / "NVC - BaseUI"
    if not ui_dir.exists():
        warn("Frontend source not found — skipping UI build")
        return

    # Check for Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError
        step(f"Node.js {result.stdout.strip()} detected")
    except FileNotFoundError:
        warn(
            "Node.js not found — skipping UI build (install Node 20+ for web dashboard)"
        )
        return

    step("Installing frontend dependencies...")
    subprocess.run(
        ["npm", "install"],
        cwd=str(ui_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    step("Building web dashboard...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(ui_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        step("Web dashboard built successfully")
    else:
        warn(f"UI build failed: {result.stderr[:200]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NeuralVaultCore v1.0 Installer")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmations")
    args = parser.parse_args()

    print(BANNER)
    print(SEP)
    print("  NeuralVaultCore v1.0 — Installation Wizard")
    print(SEP)
    print()

    if not args.yes:
        if input("  Proceed? [Y/n]: ").strip().lower() == "n":
            print("  Aborted.")
            sys.exit(0)

    print()
    print(f"  Platform: {platform.system()} {platform.machine()}")
    check_python()

    # Profile selection
    if not args.yes:
        print()
        print("  Select deployment profile:")
        print("    1) Local only (stdio) — single IDE, no web UI")
        print("    2) Local + Web UI — local use with dashboard [recommended]")
        print("    3) Remote (Docker/homelab) — network access with auth")
        print()
        choice = input("  Profile [2]: ").strip() or "2"
        profile = {"1": "local-stdio", "2": "local-ui", "3": "remote-homelab"}.get(
            choice, "local-ui"
        )
    else:
        profile = "local-ui"

    python = create_venv()
    install_deps(python)
    config = generate_env(profile)
    init_db(python)
    generate_mcp_config(python)
    install_cli(python)
    build_webui()

    # Shell hooks
    if not args.yes:
        print()
        hook_choice = (
            input("  Install shell auto-capture hooks? [y/N]: ").strip().lower()
        )
        if hook_choice == "y":
            shell = "powershell" if platform.system() == "Windows" else "bash"
            step(f"Installing {shell} hooks...")
            subprocess.run(
                [str(python), "nvc.py", "install-hooks", "--shell", shell],
                capture_output=True,
            )
            step("Shell hooks installed")

    Path("data").mkdir(exist_ok=True)

    print()
    print(SEP)
    print("  ✅  Installation Complete!")
    print(SEP)
    print()

    api_key = config.get("NVC_API_KEY", "")
    if api_key:
        print("  ┌─────────────────────────────────────────────────────┐")
        print("  │                   YOUR API KEY                      │")
        print("  │                                                     │")
        print(f"  │   {api_key:<51}│")
        print("  │                                                     │")
        print("  │   ⚠  Saved in .env — never commit this file        │")
        print("  └─────────────────────────────────────────────────────┘")
        print()

    print("  Next Steps:")
    print()
    print("  1. Copy mcp_config.json into your IDE (Claude Code / Cursor)")
    print()
    print("  2. Test the CLI:")
    print('     nvc store test "Hello NeuralVaultCore v1.0"')
    print("     nvc list")
    print()
    print("  3. Launch the web dashboard:")
    print("     nvc dashboard")
    print()
    print("  4. (Optional) Run in Docker — see README.md")
    print()
    print("  5. If migrating from ContextKeep:")
    print("     nvc migrate path/to/data/memories/")
    print()

    if not args.yes:
        input("  Press Enter to exit...")


if __name__ == "__main__":
    main()
