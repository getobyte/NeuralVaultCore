# NeuralVaultCore v1.0

> Infinite Long-Term Memory for AI Agents — local, private, low-token.

NeuralVaultCore is an MCP memory server built for token efficiency. Any AI agent with MCP support (Claude Code, Cursor, OpenCode, Ollama) gets persistent memory across sessions. Single-user, local-first — your data never leaves your machine.

**Author:** getobyte | **License:** MIT | **Python 3.10+** | **MCP Compliant**

---

## Why Low-Token Matters

Every character an MCP tool returns consumes tokens from your AI agent's context window. Most memory servers waste tokens with emoji, markdown formatting, and full-content responses. NeuralVaultCore is designed from the ground up to minimize token usage.

### Token Comparison: NeuralVaultCore vs Typical MCP Memory Server

**Retrieving a memory (2KB content):**
```
Typical server (~600 tokens):
  Memory: Project Notes
  Key: project_notes
  Updated: 2026-03-25T10:30
  <entire 2KB content dumped, no truncation>

NeuralVaultCore (~250 tokens):
  api,config | 2026-03-25T10:30

  First 1000 chars of content here...
  ...(truncated)...
  Last 1000 chars here
```

**Listing 100 memories:**
```
Typical server (~5,000 tokens):
  100 entries with emoji, full titles, snippets, no pagination

NeuralVaultCore with keys_only (~500 tokens):
  20/100 memories
  auth-notes | project:myapp
  db-schema | project:myapp
  api-design | project:myapp
  ... (paginated, 20 at a time)
```

**Resuming a project (the most common operation):**
```
Typical server: 2-3 separate tool calls (~2,100 tokens)
  1. list_all_memories -> full directory
  2. retrieve_memory("_state") -> full content

NeuralVaultCore: 1 call (~400 tokens)
  get_context("project:myapp") -> _state + recent keys in one response
```

**Estimated savings: ~7x fewer tokens per session.**

---

## Features

### Core
- **9 MCP Tools** — store, retrieve, search, list, get_context, delete, versions, restore, stats
- **Low-token output** — compact pipe-delimited ASCII, zero emoji on MCP channel
- **Token control params** — `keys_only`, `view` modes (head/tail/head_tail/full), `max_chars`
- **Project continuity** — `_state` per namespace + `get_context` resumes work in one cheap call
- **Namespaces** — organize memories by project, context, or category
- **Auto-versioning** — every update saves the previous version (last 5 kept)

### Search
- **Semantic search** — sentence-transformers (optional, CPU-only, all-MiniLM-L6-v2)
- **Full-text search** — SQLite FTS5 with ranked results, LIKE fallback
- **Hybrid** — 3+ word queries trigger semantic search, shorter queries use FTS5

### Web Dashboard
- **8 views** — Dashboard, Memories, Calendar, Search, Create, Import, Export, Detail
- **Calendar view** — monthly grid with memory count per day, click-to-expand side panel
- **UI animations** — fade-in transitions, hover effects, active nav indicator
- **Dark/Cyan theme** — toggle with keyboard shortcut (press `d`)
- **React 19 + TypeScript + Tailwind 4 + shadcn**

### Automation
- **Shell hooks** — auto-capture commands (bash, zsh, PowerShell)
- **File watcher** — monitor directories for changes
- **Activity summarization** — heuristic + optional Ollama LLM
- **Daemon mode** — background process management

### Integration
- **Import** — Notion, Obsidian, Markdown, JSON, Plain Text
- **Export** — JSON + Plain Text
- **Docker** — multi-stage build with compose profiles
- **Profiles** — local-stdio, local-ui, remote-homelab
- **Migration** — built-in ContextKeep migration tool

---

## Installation

### Option 1: Installer Wizard (Recommended)

```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
python install.py
```

The wizard will:
1. Create a virtual environment
2. Install all dependencies
3. Download the semantic search model (~80MB)
4. Ask you to choose a deployment profile
5. Generate `.env` with a secure API key
6. Initialize the SQLite database
7. Build the web dashboard (if Node.js is available)
8. Optionally install shell auto-capture hooks
9. Generate `mcp_config.json` ready to paste into your IDE

For CI/automation, skip all prompts:
```bash
python install.py --yes
```

### Option 2: Manual Setup

```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[full]"

# Initialize
nvc init

# Get your MCP config
nvc print-config --client claude-code
```

### Option 3: Docker (Homelab / LAN Access)

Use this when you want to run NVC on one machine (server, Raspberry Pi, homelab) and access it from other computers on your network.

**Prerequisites:**
- **Windows 11:** Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) with WSL 2 backend enabled (Settings > General > "Use the WSL 2 based engine"). Run all commands below from PowerShell or WSL terminal.
- **Linux:** Install Docker Engine + Docker Compose.
- **macOS:** Install Docker Desktop.

**Step 1 — Clone and configure:**
```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
cp .env.example .env
```

**Step 2 — Generate an API key and edit `.env`:**
```bash
# Generate a secure API key
python -c "import secrets; print('nvc_' + secrets.token_hex(24))"
```

Open `.env` and set these three values:
```bash
NVC_PROFILE=remote-homelab
NVC_TRANSPORT=sse
NVC_API_KEY=nvc_PASTE_YOUR_GENERATED_KEY_HERE
```

**Step 3 — Start the containers:**
```bash
docker compose up -d
```

This starts two services:
- **MCP Server** on port `9998` — your AI agents connect here
- **Web Dashboard** on port `9999` — manage memories from a browser

**Step 4 — Find the server's IP address:**
```bash
# Linux
ip addr | grep "inet " | grep -v 127.0.0.1

# Windows (run in PowerShell, NOT inside WSL)
ipconfig | findstr "IPv4"
# Look for your Wi-Fi or Ethernet adapter's IPv4 address (e.g. 192.168.1.50)
# Do NOT use the WSL/vEthernet address — use your real network adapter

# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Example: your server IP is `192.168.1.50`. Docker Desktop automatically forwards ports from Windows to the containers running in WSL 2, so other devices on your LAN can connect using this IP.

**Step 5 — Access the Web Dashboard from any device on your LAN:**

Open a browser on any computer/phone on your network and go to:
```
http://192.168.1.50:9999
```

**Step 6 — Connect Claude Code / Cursor from another PC:**

On the PC where you use your IDE, add this to your MCP config:

**Claude Code** (`~/.claude.json`):
```json
{
  "mcpServers": {
    "neural-vault-core": {
      "url": "http://192.168.1.50:9998/sse",
      "headers": {
        "Authorization": "Bearer nvc_PASTE_YOUR_KEY_HERE"
      }
    }
  }
}
```

**Cursor** (Settings > MCP Servers): add the same URL and auth header.

Replace `192.168.1.50` with your server's actual IP and `nvc_PASTE_YOUR_KEY_HERE` with the API key from your `.env` file.

**Firewall:** Make sure ports `9998` and `9999` are open on the server machine. On Linux:
```bash
sudo ufw allow 9998/tcp
sudo ufw allow 9999/tcp
```

**Verify it works:**
```bash
# From another PC, test the MCP server
curl -H "Authorization: Bearer nvc_YOUR_KEY" http://192.168.1.50:9998/health
# Should return: {"status": "ok", "version": "1.0.0"}
```

---

### Connecting to Your IDE (Local Install)

If you installed locally (Option 1 or 2), copy the generated `mcp_config.json` into your IDE:

**Claude Code** (`~/.claude.json`):
```json
{
  "mcpServers": {
    "neural-vault-core": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

**Cursor** (Settings > MCP Servers): paste the same config.

Or generate it automatically:
```bash
nvc print-config --client claude-code
nvc print-config --client cursor
```

---

## MCP Tools (9)

| Tool | Key Parameters | Description |
|------|---------------|-------------|
| `store_memory` | `key`, `content`, `tags=""`, `title=""`, `namespace="default"` | Store or update memory. Auto-versions previous content. |
| `retrieve_memory` | `key`, `namespace="default"`, **`view="head_tail"`**, **`max_chars=2000`** | Get by key. Views: `head`, `tail`, `head_tail`, `full`. Truncates to save tokens. |
| `search_memories` | `query`, `namespace=""`, **`keys_only=True`**, `limit=10` | Search. `keys_only=True` returns compact directory. 3+ words uses semantic search. |
| `list_all_memories` | `namespace=""`, `limit=20`, `offset=0`, **`keys_only=False`** | Paginated directory. `keys_only=True` returns only `key\|namespace` pairs. |
| `get_context` | `namespace`, `limit=10`, **`keys_only=True`** | Project context: `_state` first, then recent. Best for resuming work. |
| `delete_memory` | `key`, `namespace="default"` | Delete memory + all versions. |
| `get_versions` | `key`, `namespace="default"` | List saved versions (max 5 kept). |
| `restore_version` | `key`, `namespace="default"`, `version=1` | Restore previous version. Current is auto-versioned first. |
| `get_stats` | `verbose=False` | Storage statistics + top tool request counts. |

All MCP responses are **pipe-delimited ASCII**. No emoji, no markdown, no JSON bloat.

### Low-Token Workflow Example

```
1. Resume work:     get_context("project:myapp")
                    -> returns _state content + 10 recent memory keys (~400 tokens)

2. Find a memory:   search_memories("auth middleware", keys_only=True)
                    -> returns matching keys only (~200 tokens)

3. Read it:          retrieve_memory("auth-notes", view="head_tail", max_chars=1000)
                    -> returns first 500 + last 500 chars (~300 tokens)

4. Save progress:    store_memory("_state", "Refactoring auth. Next: add OAuth.", namespace="project:myapp")
                    -> returns confirmation (~30 tokens)

Total: ~930 tokens for a full resume-find-read-save cycle.
```

Compare with a typical memory server: the same cycle costs ~5,000+ tokens.

### What the Output Looks Like

**`search_memories("auth", keys_only=True)`:**
```
3 results | auth
auth-notes | Auth middleware design | project:myapp | api,auth | 2026-03-25T10:30
oauth-flow | OAuth 2.0 implementation | project:myapp | auth,oauth | 2026-03-24T14:15
jwt-config | JWT configuration | project:myapp | auth,jwt | 2026-03-23T09:00
```

**`retrieve_memory("auth-notes", view="head_tail", max_chars=500)`:**
```
api,auth | 2026-03-25T10:30

## Auth Middleware Design
- Bearer token validation
- Rate limiting per IP
...(truncated)...
- TODO: Add refresh token rotation
- See also: oauth-flow, jwt-config
```

**`get_context("project:myapp", keys_only=True)`:**
```
_state | 2026-03-25T11:00 | 150 chars
Working on auth refactor. OAuth integration next. Tests passing.
---
5/12 recent in project:myapp:
auth-notes | Auth middleware design | api,auth | 2026-03-25T10:30
oauth-flow | OAuth 2.0 implementation | auth,oauth | 2026-03-24T14:15
db-schema | Database schema v3 | db,schema | 2026-03-23T16:45
api-design | REST API endpoints | api,design | 2026-03-22T09:30
deploy-notes | Deployment checklist | ops,deploy | 2026-03-21T08:00
```

No emoji. No markdown. No wasted tokens.

---

## Web Dashboard

Start the dashboard:
```bash
nvc dashboard
# Open http://localhost:9999
```

**8 Views:**

| View | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Stats cards (memories, chars, namespaces, DB size) + recent memories |
| Memories | `/memories` | Paginated table with namespace filter |
| Calendar | `/calendar` | Monthly grid showing memory activity per day, click to expand |
| Search | `/search` | Full-text and semantic search with result cards |
| Create | `/new` | Form to create new memories with namespace and tag support |
| Import | `/import` | Import from JSON file or paste text |
| Export | `/export` | Export to JSON or plain text with namespace filter |
| Detail | `/memories/:key` | Full memory view with metadata, tags, delete option |

---

## CLI Commands (30+)

### Core
```bash
nvc store <key> <content> [--tags t1,t2] [--title "..."] [--ns default]
nvc get <key> [--ns default]
nvc search <query> [--ns ...]
nvc list [--ns ...] [--limit 50] [--offset 0]
nvc delete <key> [-y]
nvc versions <key>
nvc restore <key> <version> [-y]
nvc namespaces
nvc stats
```

### Project Workflow
```bash
nvc checkpoint <namespace> <content>
# Example:
nvc checkpoint project:myapp "Working on feature X. Next: test edge cases."
```

### Import / Export
```bash
nvc import-from obsidian /path/to/vault
nvc import-from notion export.zip
nvc import-from markdown /path/to/docs
nvc import-from text notes.txt
nvc import-from json data.json
nvc export [output.json]
nvc import input.json
```

### Server & Dashboard
```bash
nvc serve [--transport stdio|sse] [--host] [--port]
nvc dashboard [--host] [--port 9999]
nvc print-config [--client claude-code|cursor]
```

### Operations
```bash
nvc init                    # First-time setup (runs install wizard)
nvc doctor                  # Diagnostic checks
nvc repair                  # Maintenance + optimization
nvc setup-model             # Download semantic search model (~80MB)
nvc backup [output.db]
nvc restore-backup file.db [-y]
```

### Automation
```bash
nvc install-hooks [--shell bash|zsh|powershell]
nvc uninstall-hooks
nvc summarize [--hours 1] [--llm]
nvc watch /path [--ns project:name]
nvc daemon start|stop|status
```

### Migration
```bash
nvc migrate /path/to/contextkeep/data/memories/
```

---

## Profiles

| Profile | Transport | Auth | MCP Port | UI Port | Use Case |
|---------|-----------|------|----------|---------|----------|
| `local-stdio` | stdio | off | 9998 | 9999 | Single IDE, local only |
| `local-ui` | stdio | off | 9998 | 9999 | Local + web dashboard |
| `remote-homelab` | sse | required | 9998 | 9999 | Docker, LAN, Raspberry Pi |

Set via `NVC_PROFILE` in `.env` or as an environment variable.

---

## Configuration

```bash
# .env
NVC_PROFILE=local-stdio           # local-stdio | local-ui | remote-homelab
NVC_DB_PATH=./data/nvc.db
NVC_API_KEY=nvc_...               # Required for remote-homelab (auto-generated)
NVC_PORT=9998                     # MCP server port
NVC_UI_PORT=9999                  # Web dashboard port
NVC_LOG_TOKENS=true               # Log token estimates per tool call
NVC_LOG_JSON=true                 # Structured JSON logging
NVC_SNIPPET_LENGTH=250            # Snippet truncation length
NVC_SEARCH_LIMIT=50               # Max search results
NVC_MAX_VERSIONS_KEPT=5           # Versions per memory
```

Precedence: CLI flags > env vars > profile defaults > built-in defaults.

---

## Architecture

```
NeuralVaultCore/
├── core/
│   ├── config.py          # Config + profiles + constants
│   ├── models.py          # Memory, Version, StorageStats dataclasses
│   ├── storage.py         # SQLite + WAL + FTS5 + embeddings
│   ├── service.py         # Shared business logic (MCP/CLI/UI)
│   ├── auth.py            # API key + Bearer token middleware
│   ├── migration.py       # Schema versioning + ContextKeep migration
│   ├── exceptions.py      # NVCError, ValidationError, StorageError
│   ├── importers.py       # Notion/Obsidian/Markdown/JSON/Text importers
│   ├── summarizer.py      # Activity summarization (heuristic + Ollama)
│   ├── doctor.py          # Diagnostic checks
│   ├── repair.py          # Database maintenance
│   ├── watcher.py         # File system watcher
│   ├── daemon.py          # Background process manager
│   └── shell_capture.py   # Shell hook handler
├── hooks/                 # bash, zsh, PowerShell, systemd, Windows service
├── tests/                 # 112 automated tests (pytest)
├── NVC - BaseUI/          # React 19 + TypeScript + Tailwind 4 + shadcn
├── server.py              # MCP server (9 tools, auth, token logging)
├── nvc.py                 # CLI tool (30+ commands)
├── webui.py               # Web backend (10 REST endpoints + SPA)
├── install.py             # Installer wizard
├── Dockerfile             # Multi-stage build (Node UI + Python)
└── docker-compose.yml     # 2 services (MCP + WebUI)
```

---

## Security

- **API keys** — `secrets.token_hex(24)` with `nvc_` prefix (52 chars)
- **Constant-time comparison** — `secrets.compare_digest` prevents timing attacks
- **Auth required** for `remote-homelab` profile (Bearer token on every request)
- **stdio transport** — implicit local trust, no auth needed
- **Parameterized SQL** — zero injection surface
- **Input validation** — strict limits on key, title, content, tags length
- **Path traversal protection** — SPA fallback validates all file paths
- **Docker** — non-root user, no hardcoded credentials
- **Zero cloud, zero telemetry** — all data stays local

---

## Storage Limits

| Field | Max |
|-------|-----|
| Key | 256 chars |
| Title | 512 chars |
| Content | 1 MB |
| Tags | 1,024 chars |
| Versions | 5 per key |
| Search results | 50 per query |
| Snippet | 250 chars |

---

## Migrating from ContextKeep

If you're coming from ContextKeep, NeuralVaultCore includes a built-in migration tool:

```bash
nvc migrate /path/to/contextkeep/data/memories/
```

This imports all your ContextKeep JSON memory files into NeuralVaultCore's SQLite database with full metadata preservation.

---

**NeuralVaultCore v1.0** — Cyber-Draco Legacy | built by getobyte
