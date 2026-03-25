# NeuralVaultCore v1.0

> Infinite Long-Term Memory for AI Agents — local, private, low-token.

NeuralVaultCore is an MCP memory server built for token efficiency. Any AI agent with MCP support (Claude Code, Cursor, OpenCode, Ollama) gets persistent memory across sessions. Single-user, local-first — your data never leaves your machine.

**Author:** getobyte | **License:** MIT | **Python 3.10+** | **MCP Compliant**

---

## 🤖 Official AI Agent Skills (Ecosystem)

An MCP server is only as good as the AI using it. To get the absolute best performance, zero context bloat, and perfect autonomy from your agents, we provide two official system prompts (skills):

* ⚡ **[NeuralVaultSkill](https://github.com/getobyte/NeuralVaultSkill)**: The "Daily Driver". An ultra-compact (~383 tokens) system prompt that teaches your agent how to autonomously save project context silently, use token-saving tools (`head_tail`, `keys_only`), and enforce strict namespace isolation (`project:<repo-name>`).
* 🧹 **[NeuralVaultArchivist](https://github.com/getobyte/NeuralVaultArchivist)**: The "Maintenance Tool". An on-demand consolidation skill. Run this manually to safely merge overlapping memory fragments into compact Master Records without deleting any data.

---

## Why Low-Token Matters

Every character an MCP tool returns consumes tokens from your AI agent's context window. Most memory servers waste tokens with emoji, markdown formatting, and full-content responses. NeuralVaultCore is designed from the ground up to minimize token usage.

### Token Comparison: NeuralVaultCore vs Typical MCP Memory Server

**Retrieving a memory (2KB content):**

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

**Listing 100 memories:**

Typical server (~5,000 tokens):
  100 entries with emoji, full titles, snippets, no pagination

NeuralVaultCore with keys_only (~500 tokens):
  20/100 memories
  auth-notes | project:myapp
  db-schema | project:myapp
  api-design | project:myapp
  ... (paginated, 20 at a time)

---

## Installation

### Option 1: Installer Wizard (Recommended)

$ git clone https://github.com/getobyte/NeuralVaultCore.git
$ cd NeuralVaultCore
$ python install.py

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
$ python install.py --yes

### Option 2: Manual Setup

$ git clone https://github.com/getobyte/NeuralVaultCore.git
$ cd NeuralVaultCore

# Create virtual environment
$ python -m venv venv
$ source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate     # Windows

# Install dependencies
$ pip install -e ".[full]"

# Initialize
$ nvc init

# Get your MCP config
$ nvc print-config --client claude-code

### Option 3: Docker (Homelab / LAN Access)

Use this when you want to run NVC on one machine (server, Raspberry Pi, homelab) and access it from other computers on your network.

**Prerequisites:**
- **Windows 11:** Install Docker Desktop with WSL 2 backend enabled.
- **Linux:** Install Docker Engine + Docker Compose.
- **macOS:** Install Docker Desktop.

**Step 1 — Clone and configure:**
$ git clone https://github.com/getobyte/NeuralVaultCore.git
$ cd NeuralVaultCore
$ cp .env.example .env

**Step 2 — Generate an API key and edit `.env`:**
$ python -c "import secrets; print('nvc_' + secrets.token_hex(24))"

Open `.env` and set these three values:
NVC_PROFILE=remote-homelab
NVC_TRANSPORT=sse
NVC_API_KEY=nvc_PASTE_YOUR_GENERATED_KEY_HERE

**Step 3 — Start the containers:**
$ docker compose up -d

This starts two services:
- **MCP Server** on port `9998` — your AI agents connect here
- **Web Dashboard** on port `9999` — manage memories from a browser

**Step 4 — Find the server's IP address:**
# Linux: ip addr | grep "inet " | grep -v 127.0.0.1
# Windows: ipconfig | findstr "IPv4"
# macOS: ifconfig | grep "inet " | grep -v 127.0.0.1

**Step 5 — Access the Web Dashboard:**
Open a browser on any computer/phone on your network and go to:
http://<YOUR_SERVER_IP>:9999

---

## 🔗 Connecting to Your IDE

### Local Install (Options 1 & 2)
Copy the generated `mcp_config.json` into your IDE or run:
$ nvc print-config --client cursor
$ nvc print-config --client claude-code

### Remote/Docker (Option 3)
Add this to your MCP config (e.g., `~/.claude.json`):
{
  "mcpServers": {
    "neural-vault-core": {
      "url": "http://<YOUR_SERVER_IP>:9998/sse",
      "headers": {
        "Authorization": "Bearer nvc_PASTE_YOUR_KEY_HERE"
      }
    }
  }
}

---

## Features

### Core
* **9 MCP Tools** — store, retrieve, search, list, get_context, delete, versions, restore, stats
* **Low-token output** — compact pipe-delimited ASCII, zero emoji on MCP channel
* **Token control params** — `keys_only`, `view` modes (head/tail/head_tail/full), `max_chars`
* **Project continuity** — `_state` per namespace + `get_context` resumes work in one cheap call
* **Namespaces** — organize memories by project, context, or category
* **Auto-versioning** — every update saves the previous version (last 5 kept)

### Search
* **Semantic search** — sentence-transformers (optional, CPU-only, all-MiniLM-L6-v2)
* **Full-text search** — SQLite FTS5 with ranked results, LIKE fallback
* **Hybrid** — 3+ word queries trigger semantic search, shorter queries use FTS5

---

## CLI Commands (30+)

nvc store <key> <content> [--tags t1,t2] [--title "..."] [--ns default]
nvc get <key> [--ns default]
nvc search <query> [--ns ...]
nvc list [--ns ...] [--limit 50] [--offset 0]
nvc delete <key> [-y]
nvc versions <key>
nvc restore <key> <version> [-y]
nvc dashboard [--host] [--port 9999]

---

## Security

* **API keys** — `secrets.token_hex(24)` with `nvc_` prefix (52 chars)
* **Constant-time comparison** — `secrets.compare_digest` prevents timing attacks
* **Auth required** for `remote-homelab` profile (Bearer token on every request)
* **stdio transport** — implicit local trust, no auth needed
* **Zero cloud, zero telemetry** — all data stays local

---

## Storage Limits

| Field | Max |
| --- | --- |
| Key | 256 chars |
| Content | 1 MB |
| Versions | 5 per key |
| Search results | 50 per query |

---

**NeuralVaultCore v1.0** — Cyber-Draco Legacy | built by [getobyte](https://github.com/getobyte)
