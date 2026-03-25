================================================================================
# NeuralVaultCore v1.0
================================================================================
> Infinite Long-Term Memory for AI Agents — local, private, low-token.

NeuralVaultCore is an MCP memory server built for token efficiency. Any AI agent 
with MCP support (Claude Code, Cursor, OpenCode, Ollama) gets persistent memory 
across sessions. Single-user, local-first — your data never leaves your machine.

**Author:** getobyte | **License:** MIT | **Python 3.10+** | **MCP Compliant**

---

## 🤖 Official AI Agent Skills (Ecosystem)

An MCP server is only as good as the AI using it. To get the absolute best 
performance, zero context bloat, and perfect autonomy from your agents, we 
provide two official system prompts (skills):

* ⚡ **[NeuralVaultSkill](https://github.com/getobyte/NeuralVaultSkill)**: 
  The "Daily Driver". An ultra-compact (~383 tokens) system prompt that teaches 
  your agent how to autonomously save project context silently, use token-saving 
  tools (`head_tail`, `keys_only`), and enforce strict namespace isolation.

* 🧹 **[NeuralVaultArchivist](https://github.com/getobyte/NeuralVaultArchivist)**: 
  The "Maintenance Tool". An on-demand consolidation skill. Run this manually 
  to safely merge overlapping memory fragments into compact Master Records 
  without deleting any data.

---

## Why Low-Token Matters

Every character an MCP tool returns consumes tokens from your AI agent's 
context window. NeuralVaultCore is designed to minimize usage by up to 7x.

### Token Comparison: NeuralVaultCore vs Typical MCP Memory Server

**Retrieving a memory (2KB content):**
- Typical server (~600 tokens): Full content dump + heavy JSON metadata.
- NeuralVaultCore (~250 tokens): Returns pipe-delimited Head/Tail views.

**Listing 100 memories:**
- Typical server (~5,000 tokens): All entries with emojis, titles, snippets.
- NeuralVaultCore with keys_only (~500 tokens): Returns `key|namespace` only.

**Resuming a project (the most common operation):**
- Typical server (~2,100 tokens): 2-3 separate tool calls (list + retrieve).
- NeuralVaultCore: 1 call (~400 tokens) via `get_context`.

---

## Installation

### Option 1: Installer Wizard (Recommended)
$ git clone https://github.com/getobyte/NeuralVaultCore.git
$ cd NeuralVaultCore
$ python install.py

The wizard handles: venv, dependencies, search model, .env, DB init, 
web dashboard build, and mcp_config.json generation.
(Use --yes for headless/CI installation).

### Option 2: Manual Setup
$ python -m venv venv
$ source venv/bin/activate (or venv\Scripts\activate on Windows)
$ pip install -e ".[full]"
$ nvc init
$ nvc print-config --client claude-code

### Option 3: Docker (Homelab / LAN Access)
Use this to run NVC on a server/NAS and access it from your network.

Step 1 — Configure:
$ cp .env.example .env

Step 2 — Generate API Key:
$ python -c "import secrets; print('nvc_' + secrets.token_hex(24))"
(Paste key in .env at NVC_API_KEY and set NVC_PROFILE=remote-homelab)

Step 3 — Start:
$ docker compose up -d

Step 4 — Find IP:
Linux:   ip addr | grep "inet "
Windows: ipconfig | findstr "IPv4" (Run in PowerShell)

---

## 🔗 Connecting to Your IDE

### Local Install (Options 1 & 2):
$ nvc print-config --client cursor
$ nvc print-config --client claude-code

### Remote/Docker (Option 3):
Add to your MCP config:
{
  "mcpServers": {
    "neural-vault-core": {
      "url": "http://<SERVER_IP>:9998/sse",
      "headers": { "Authorization": "Bearer nvc_YOUR_KEY" }
    }
  }
}

---

## MCP Tools (The Core 9)

1. store_memory    : Save/Update. Auto-versions (last 5 kept).
2. retrieve_memory : Read. Supports view="head_tail" and max_chars.
3. search_memories : Hybrid Search. 3+ words trigger semantic search.
4. list_all_memories : Paginated directory. Use keys_only=True to save tokens.
5. get_context     : Rapid resume. Loads _state + recent history in one call.
6. delete_memory   : Permanent deletion of key and all versions.
7. get_versions    : Audit version history.
8. restore_version : Rollback to a previous state.
9. get_stats       : Database and tool usage statistics.

---

## Web Dashboard (8 Views)

Start: $ nvc dashboard (Default: http://localhost:9999)

- Dashboard: Overview cards and activity stats.
- Memories: Full table with advanced namespace filtering.
- Calendar: Monthly contribution grid (click to expand).
- Search: Dedicated semantic/FTS5 search interface.
- Create/Import/Export: Manual data management (JSON/Markdown/Text).
- Detail: Metadata inspector per memory.
- Theme: Dark/Cyan (Toggle with 'd' key).

---

## CLI Commands (30+)

CORE:
$ nvc store <key> <content> [--tags t1] [--title "Text"] [--ns default]
$ nvc get <key> [--ns default]
$ nvc search <query> [--ns ...]
$ nvc stats

WORKFLOW:
$ nvc checkpoint <namespace> "Feature X complete. Next: testing."

IMPORT/EXPORT:
$ nvc import-from obsidian /path/to/vault
$ nvc import-from notion export.zip
$ nvc import-from markdown /path/to/folder
$ nvc export [output.json]

OPERATIONS:
$ nvc doctor       # System diagnostics
$ nvc repair       # DB maintenance and optimization
$ nvc backup       # Quick DB backup

AUTOMATION:
$ nvc install-hooks # Auto-capture shell commands (bash/zsh/ps)
$ nvc watch /path   # Monitor files for changes
$ nvc daemon start  # Background process management

---

## Architecture & Security

FOLDER STRUCTURE:
- core/        : Business logic (storage, auth, importers, doctor).
- hooks/       : Shell/systemd integration scripts.
- NVC-BaseUI/  : React 19 + TypeScript + Tailwind 4 + shadcn.
- server.py    : MCP server entry point (stdio/sse).

SECURITY:
- API Keys: nvc_ prefix, constant-time comparison.
- Auth: Required for remote-homelab (Bearer token).
- local-first: Zero telemetry, zero cloud. Your data stays on-prem.

STORAGE LIMITS:
- Key: 256 chars | Title: 512 chars | Content: 1 MB | Versions: 5.

================================================================================
NeuralVaultCore v1.0 — Cyber-Draco Legacy | built by getobyte
================================================================================
