<div align="center">
  <a href="https://github.com/getobyte/NeuralVaultCore">
    <img src="https://github.com/getobyte/NeuralVaultCore/raw/main/NVC-logo.png" width="260"/>
  </a>

# NeuralVaultCore v1.0

**Infinite long-term memory for AI agents — local, private, low-token.**

Any AI agent with MCP support gets persistent memory across sessions.  
Single-user, local-first. Your data never leaves your machine.

![Python](https://img.shields.io/badge/Python-3.10+-0D1117?style=flat-square&logo=python&logoColor=4488FF)
![License](https://img.shields.io/badge/License-MIT-0D1117?style=flat-square&logo=opensourceinitiative&logoColor=4CAF50)
![MCP](https://img.shields.io/badge/MCP-Compliant-0D1117?style=flat-square&logo=anthropic&logoColor=9F7AEA)

</div>

---

## 🌐 Ecosystem

NeuralVaultCore is the foundation. Build on top of it with the full NeuralVault stack:

| Component | Role |
|-----------|------|
| 🧠 **NeuralVaultCore** *(you are here)* | MCP memory server — the brain |
| ⚡ [**NeuralVaultSkill**](https://github.com/getobyte/NeuralVaultSkill) | Session memory automation — `/nvc:init` + `/nvc:end` |
| 🧹 [**NeuralVaultArchivist**](https://github.com/getobyte/NeuralVaultArchivist) | Memory consolidation — on-demand cleanup |
| 🛠️ [**NeuralSkillBuilder**](https://github.com/getobyte/NeuralSkillBuilder) | Skill builder — design, scaffold and audit Claude Code skills |
| 🔄 [**NeuralVaultFlow**](https://github.com/getobyte/NeuralVaultFlow) | Dev workflow — brainstorm, plan, execute, audit, deploy |

> **⚠️ Prerequisites**  
> NeuralVaultCore is the memory server — but without a skill prompt, your agent won't know how to use it efficiently.  
> At minimum, install **[NeuralVaultSkill](https://github.com/getobyte/NeuralVaultSkill)** alongside this server.

---

## 💡 Why Low-Token Matters

Most MCP servers waste thousands of tokens on verbose output.  
NeuralVaultCore cuts overhead by up to **7×** using smart truncation and pipe-delimited ASCII responses.

---

## ✨ Features

### 🧠 Core Memory
- Persistent long-term memory across sessions — agents remember everything
- Local-first SQLite storage — zero cloud, zero telemetry
- Namespace separation for clean project/context isolation
- `_state` checkpoint memory for instant project continuity
- Automatic version history (up to 5 versions per record) with restore support
- Storage statistics and health visibility

### 🤖 MCP / Agent Tools
- Full tool suite: `store_memory`, `retrieve_memory`, `search_memories`, `list_all_memories`, `get_context`, `delete_memory`, `get_versions`, `restore_version`, `get_stats`
- Token-efficient compact responses — up to **7× less overhead**
- Output truncation and view modes (`head_tail`, `full`)
- Full-text search (FTS5) + optional semantic search (all-MiniLM-L6-v2)
- SSE transport with Bearer-token authentication for remote access

### 🖥️ Web Dashboard

<div align="center">
  <img src="https://github.com/getobyte/NeuralVaultCore/raw/main/Screenshots/dashboard.png" width="800"/>
  <p><em>Dashboard — totals, DB size, namespaces and recent memories</em></p>
</div>

<div align="center">
  <img src="https://github.com/getobyte/NeuralVaultCore/raw/main/Screenshots/Memories.png" width="800"/>
  <p><em>Memories — full directory with namespace filter, tags and pagination</em></p>
</div>

<div align="center">
  <img src="https://github.com/getobyte/NeuralVaultCore/raw/main/Screenshots/calendar.png" width="800"/>
  <p><em>Calendar — monthly memory timeline with day drill-down</em></p>
</div>

- **Dashboard** — totals, DB size, namespaces and recent memories at a glance
- **Memories** — full directory with namespace filter, tags, pagination
- **Memory detail** — metadata, tags, content view, version history, delete
- **Calendar** — monthly timeline with day drill-down
- **Search** — interactive full-text memory lookup
- **New Memory** — manual memory entry
- **Import** — JSON, Markdown, Obsidian, Notion, plain text
- **Export** — preview and download
- Theme switching and keyboard shortcuts

### ⚙️ Automation & Capture
- Shell command auto-capture for Bash, Zsh and PowerShell
- File watcher for directory changes
- Activity summarization
- Background daemon mode with automatic daily backups

### 📥 Import / Export
- Import from: JSON, plain text, Markdown folders, Obsidian vaults, Notion exports
- Export to: JSON and plain text
- Migration from ContextKeep JSON (`nvc migrate`)

### 🔧 Admin & Maintenance
- Installer wizard — venv, deps, search model, MCP config, all automated
- Config generation for Claude Code, Cursor, VS Code, OpenCode
- `nvc doctor` — diagnostic checks
- `nvc repair` — DB maintenance and optimization
- `nvc backup` / `nvc restore-backup` — manual backup and restore
- Schema migration support

---

## 🔌 Ports

| Service | Port | URL |
|---------|------|-----|
| MCP Server | `9998` | `http://localhost:9998/sse` |
| Web Dashboard | `9999` | `http://localhost:9999` |

---

## 🚀 Installation

### Option 1 — Installer Wizard *(Recommended)*

```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
python install.py
```

The wizard will:
1. Create a Python virtual environment
2. Install all dependencies
3. Download the semantic search model (~80 MB)
4. Generate `.env` with a secure API key
5. Initialize the SQLite database
6. Generate `mcp_config.json` for your IDE
7. Ask which deployment profile to use
8. Ask if you want shell auto-capture hooks

**Deployment profiles:**

| Profile | Use case |
|---------|---------|
| `local-stdio` | Single IDE, no web UI, simplest setup |
| `local-ui` | Local use + web dashboard on `localhost:9999` *(recommended)* |
| `remote-homelab` | Network access with Bearer-token auth + Docker |

---

### Option 2 — Manual Setup

```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
python -m venv venv

source venv/bin/activate    # Linux / macOS
venv\Scripts\activate       # Windows

pip install -e ".[full]"
nvc init
nvc print-config --client claude-code
```

---

### Option 3 — Docker *(LAN / Homelab)*

**Step 1** — Clone and configure:
```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
cp .env.example .env
```

**Step 2** — Generate an API key and paste it into `.env` at `NVC_API_KEY`:
```bash
python -c "import secrets; print('nvc_' + secrets.token_hex(24))"
```

**Step 3** — Start the containers:
```bash
docker compose up -d
```

This starts two services:
- `nvc-mcp` — MCP server on port `9998`
- `nvc-webui` — Web dashboard on port `9999`

**Step 4** — Find your server IP:
```bash
ip addr | grep "inet " | grep -v 127.0.0.1   # Linux
ipconfig | findstr "IPv4"                      # Windows
ifconfig | grep "inet " | grep -v 127.0.0.1   # macOS
```

---

## 🔗 Connecting to Your Client

NeuralVaultCore works with any MCP-compatible client. Choose your setup below.

---

### Claude Code *(CLI)*

Generate config automatically:
```bash
nvc print-config --client claude-code
```

Or add manually to `~/.claude.json`:

**Local (stdio):**
```json
{
  "mcpServers": {
    "neural-vault-core": {
      "command": "/path/to/NeuralVaultCore/venv/bin/python",
      "args": ["/path/to/NeuralVaultCore/server.py"]
    }
  }
}
```

**Remote / Docker (SSE):**
```json
{
  "mcpServers": {
    "neural-vault-core": {
      "url": "http://<YOUR_SERVER_IP>:9998/sse",
      "headers": {
        "Authorization": "Bearer nvc_YOUR_API_KEY"
      }
    }
  }
}
```

Then install the skill:
```bash
npx github:getobyte/NeuralVaultSkill --global
```

Restart Claude Code and use `/nvc:init` to start a session.

---

### Cursor

Generate config automatically:
```bash
nvc print-config --client cursor
```

Or add manually to `.cursor/mcp.json` (global) or `<project>/.cursor/mcp.json` (local):

**Local (stdio):**
```json
{
  "mcpServers": {
    "neural-vault-core": {
      "command": "/path/to/NeuralVaultCore/venv/bin/python",
      "args": ["/path/to/NeuralVaultCore/server.py"]
    }
  }
}
```

**Remote / Docker (SSE):**
```json
{
  "mcpServers": {
    "neural-vault-core": {
      "url": "http://<YOUR_SERVER_IP>:9998/sse",
      "headers": {
        "Authorization": "Bearer nvc_YOUR_API_KEY"
      }
    }
  }
}
```

Then install the skill — paste the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) into Cursor's **System Prompt** or run:
```bash
curl -sL https://raw.githubusercontent.com/getobyte/NeuralVaultSkill/main/SKILL.md > .cursorrules
```

---

### VS Code *(with Copilot / Continue / Cline)*

Generate config:
```bash
nvc print-config --client vscode
```

Or add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "neural-vault-core": {
      "type": "stdio",
      "command": "/path/to/NeuralVaultCore/venv/bin/python",
      "args": ["/path/to/NeuralVaultCore/server.py"]
    }
  }
}
```

For **Continue** extension, add to `~/.continue/config.json`:
```json
{
  "mcpServers": [
    {
      "name": "neural-vault-core",
      "command": "/path/to/NeuralVaultCore/venv/bin/python",
      "args": ["/path/to/NeuralVaultCore/server.py"]
    }
  ]
}
```

For **Cline** extension, add via Settings → Cline → MCP Servers.

Paste the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) into your extension's system prompt field.

---

### OpenCode

Generate config:
```bash
nvc print-config --client opencode
```

Or add to `~/.config/opencode/config.json`:

```json
{
  "mcp": {
    "neural-vault-core": {
      "command": "/path/to/NeuralVaultCore/venv/bin/python",
      "args": ["/path/to/NeuralVaultCore/server.py"]
    }
  }
}
```

Paste the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) into your system prompt.

---

### Ollama *(with Open WebUI or AnythingLLM)*

Ollama itself does not implement MCP natively. Connect via **Open WebUI** or **AnythingLLM** which both support MCP tool servers.

Start NeuralVaultCore in SSE mode:
```bash
nvc serve --transport sse --host 0.0.0.0 --port 9998
```

Then configure your frontend to point to `http://localhost:9998/sse` (see Open WebUI and AnythingLLM sections below).

Paste the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) into your model's system prompt in the UI.

---

### Open WebUI

Start NeuralVaultCore in SSE mode first:
```bash
nvc serve --transport sse --host 0.0.0.0 --port 9998
```

In Open WebUI:
1. Go to **Settings → Tools** (or **Admin → Tools**)
2. Click **Add Tool Server**
3. Set URL to `http://localhost:9998/sse`
4. If auth is enabled, add header: `Authorization: Bearer nvc_YOUR_API_KEY`
5. Save and enable the tool server

Then in any chat, click the tools icon and enable `neural-vault-core`.

Paste the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) into your model's system prompt.

---

### LM Studio

Start NeuralVaultCore in SSE mode:
```bash
nvc serve --transport sse --host 0.0.0.0 --port 9998
```

In LM Studio:
1. Go to **Developer → MCP Servers**
2. Click **Add MCP Server**
3. Set type to **SSE**
4. Set URL to `http://localhost:9998/sse`
5. If auth is enabled, add the Authorization header

Paste the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) into the **System Prompt** field of your chat preset.

---

### OpenAI Codex CLI

Start NeuralVaultCore in SSE mode:
```bash
nvc serve --transport sse --host 0.0.0.0 --port 9998
```

Add to your Codex config (`~/.codex/config.toml` or equivalent):
```toml
[[mcp_servers]]
name = "neural-vault-core"
url = "http://localhost:9998/sse"

[mcp_servers.headers]
Authorization = "Bearer nvc_YOUR_API_KEY"
```

Paste the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) into your system prompt instructions file.

---

### AnythingLLM

Start NeuralVaultCore in SSE mode:
```bash
nvc serve --transport sse --host 0.0.0.0 --port 9998
```

In AnythingLLM:
1. Go to **Settings → Agent Skills → Custom MCP Servers**
2. Add a new server with URL `http://localhost:9998/sse`
3. If auth is enabled, add: `Authorization: Bearer nvc_YOUR_API_KEY`
4. Enable the server

Paste the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) into the workspace system prompt.

---

### Any MCP-Compatible Client (Generic)

Start the server in the appropriate mode:

```bash
# stdio mode (local, single process)
nvc serve --transport stdio

# SSE mode (remote, network accessible)
nvc serve --transport sse --host 0.0.0.0 --port 9998
```

**stdio config:**
```json
{
  "mcpServers": {
    "neural-vault-core": {
      "command": "python",
      "args": ["/path/to/NeuralVaultCore/server.py"]
    }
  }
}
```

**SSE config:**
```json
{
  "mcpServers": {
    "neural-vault-core": {
      "url": "http://localhost:9998/sse",
      "headers": {
        "Authorization": "Bearer nvc_YOUR_API_KEY"
      }
    }
  }
}
```

Then paste [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) contents into your agent's system prompt.

---

## ⚡ Installing NeuralVaultSkill

NeuralVaultSkill teaches your agent how to use NeuralVaultCore efficiently — when to save, how to resume, and how to stay within token limits.

### Claude Code (slash commands)

```bash
npx github:getobyte/NeuralVaultSkill --global    # all workspaces
npx github:getobyte/NeuralVaultSkill --local     # current project only
```

This installs `/nvc:init` and `/nvc:end` as slash commands in Claude Code.

### Cursor / VS Code / Any IDE

```bash
curl -sL https://raw.githubusercontent.com/getobyte/NeuralVaultSkill/main/SKILL.md > .cursorrules
```

Or copy [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) manually and paste into your IDE's system prompt field.

### Ollama / LM Studio / Open WebUI / AnythingLLM

Copy the full contents of [SKILL.md](https://github.com/getobyte/NeuralVaultSkill/blob/main/SKILL.md) and paste it into the **System Prompt** of your model or chat preset. The skill is plain text — it works with any model that follows instructions.

### Usage

```
/nvc:init  →  loads project context at session start
/nvc:end   →  saves a short _state checkpoint at session end
```

Between those two commands, the agent saves important decisions autonomously in the background.

---

## 🧹 NeuralVaultArchivist — Memory Consolidation

Over time, memories accumulate. The Archivist consolidates overlapping fragments into a single canonical master record — **without deleting anything**.

### Install

Copy the contents of [SKILL.md](https://github.com/getobyte/NeuralVaultArchivist/blob/main/SKILL.md) and paste it as a **System Prompt** in a new chat session when you need to run maintenance.

### Usage

Trigger with natural language:
```
"Consolidate memories for the auth-system namespace."
"Merge all overlapping memories related to deployment."
"Clean up project:myapp memories, but do not delete anything."
```

The Archivist will:
1. Search for all related memory fragments
2. Synthesize them into one canonical master record
3. Save the consolidated record
4. Report which source memories were used and suggest cleanup candidates (without deleting)

---

## 🔄 NeuralVaultFlow — Full Dev Workflow

Once your memory is set up, use **NeuralVaultFlow** to orchestrate the full development cycle with NVC persistence baked in at every step.

```bash
npx github:getobyte/NeuralVaultFlow --global
```

| Command | What it does |
|---------|-------------|
| `/nvc:brainstorm` | Structured requirements gathering |
| `/nvc:plan` | Executable plan with acceptance criteria |
| `/nvc:execute` | Step-by-step execution with verify loops |
| `/nvc:audit` | Static analysis — dead code, errors, security |
| `/nvc:review` | Opinionated code review |
| `/nvc:seo` | Technical SEO audit |
| `/nvc:geo` | AI search visibility (GEO Score 0–100) |
| `/nvc:perf` | Performance audit |
| `/nvc:security` | OWASP Top 10 + exploit scenarios |
| `/nvc:deploy` | Pre-deployment gate — blocks on CRITICAL failures |

Every command reads from and writes to NeuralVaultCore — so your brainstorm, plans, and audit results persist across sessions automatically.

---

## 🛠️ NeuralSkillBuilder — Build Your Own Skills

Want to create custom Claude Code skills that integrate with NeuralVaultCore? Use **NeuralSkillBuilder**.

```bash
npx github:getobyte/NeuralSkillBuilder --global
```

| Command | What it does |
|---------|-------------|
| `/nvc:skill discover` | Guided 6-phase interview to design a new skill |
| `/nvc:skill scaffold` | Generate a complete skill directory from a spec |
| `/nvc:skill distill` | Transform raw knowledge into framework chunks |
| `/nvc:skill audit` | Check compliance against NVC skill conventions |

The discovery phase includes a dedicated step for designing NVC integration — which keys to read, which events trigger saves, and what namespace convention to use.

---

## 🛠️ CLI Reference

### Core Operations

```bash
nvc store <key> <content> [--tags t1,t2] [--ns default]
nvc get <key> [--ns default]
nvc search <query> [--ns ...]
nvc list [--limit 50] [--keys_only]
nvc delete <key> [--ns default] [--yes]
nvc stats
nvc namespaces
```

### Versioning

```bash
nvc versions <key> [--ns default]
nvc restore <key> <version> [--ns default]
```

### Workflow

```bash
nvc checkpoint <namespace> <content>
# Example:
nvc checkpoint project:myapp "Finished auth refactor. Next: write tests."
```

### Import / Export

```bash
nvc export [output.json]
nvc import <file.json>
nvc import-from markdown ./docs/ [--ns project:docs]
nvc import-from obsidian ./vault/ [--ns project:notes]
nvc import-from notion ./notion-export/ [--ns project:notion]
nvc import-from text ./notes.txt
nvc import-from json ./backup.json
nvc migrate ./path/to/contextkeep/memories/
```

### Automation

```bash
nvc install-hooks --shell bash
nvc install-hooks --shell zsh
nvc install-hooks --shell powershell
nvc uninstall-hooks

nvc watch ./src/ --interval 2
nvc summarize

nvc daemon start [--watch ./src/]
nvc daemon stop
nvc daemon status
```

### Maintenance

```bash
nvc doctor
nvc repair
nvc backup [output.bak]
nvc restore-backup <file.bak>
nvc setup-model
nvc dashboard                  # Web UI → http://localhost:9999
```

### Server

```bash
nvc serve --transport stdio
nvc serve --transport sse --port 9998
nvc print-config --client claude-code
nvc print-config --client cursor
nvc print-config --client vscode
nvc print-config --client opencode
```

---

## 🏗️ Architecture

```
NeuralVaultCore/
├── core/
│   ├── storage.py       # SQLite storage engine
│   ├── service.py       # Business logic
│   ├── auth.py          # API key authentication
│   ├── config.py        # Environment config
│   ├── doctor.py        # Diagnostic checks
│   ├── repair.py        # DB optimization
│   ├── importers.py     # Notion / Obsidian / Markdown importers
│   ├── shell_capture.py # Shell hook capture
│   ├── watcher.py       # File watcher
│   ├── summarizer.py    # Activity summarizer
│   ├── daemon.py        # Background daemon
│   └── migration.py     # Schema migrations
├── hooks/
│   ├── bash_hook.sh         # Bash auto-capture
│   ├── zsh_hook.sh          # Zsh auto-capture
│   ├── powershell_hook.ps1  # PowerShell auto-capture
│   └── nvc-daemon.service   # systemd service unit
├── NVC-BaseUI/          # React 19 + TypeScript + Tailwind 4 + shadcn
├── server.py            # MCP server entry point (stdio / sse)
├── webui.py             # Web dashboard server → port 9999
├── nvc.py               # CLI entry point
└── install.py           # Installer wizard
```

---

## 🔒 Security

| Area | Details |
|------|---------|
| **API Keys** | `nvc_` prefix, 52 chars, constant-time comparison |
| **Auth** | Bearer token required for remote/homelab setups |
| **Privacy** | Zero telemetry, zero cloud, fully local |
| **Transport** | SSE over HTTP — add Nginx/Caddy reverse proxy for HTTPS in production |

---

## 📦 Storage Limits

These limits apply **per record** — total database size is only limited by your local disk space.

| Field | Per-record limit |
|-------|-----------------|
| Key | 256 chars |
| Title | 512 chars |
| Content | 1 MB |
| Versions | 5 |

---

<div align="center">

**NeuralVaultCore v1.0** — Cyber-Draco Legacy  
Built by [getobyte](https://github.com/getobyte) · Romania 🇷🇴

</div>
