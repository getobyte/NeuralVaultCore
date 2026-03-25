# 🧠 NeuralVaultCore v1.0

> **Infinite Long-Term Memory for AI Agents** — local, private, low-token.

NeuralVaultCore is an MCP memory server built for **token efficiency**. Any AI agent with MCP support (Claude Code, Cursor, OpenCode, Ollama) gets persistent memory across sessions. Single-user, local-first — your data never leaves your machine.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-Compliant-purple?style=flat-square)

---

## 🤖 Official AI Agent Skills (Ecosystem)

An MCP server is only as good as the AI using it. To get the absolute best performance, zero context bloat, and perfect autonomy, use these companion prompts:

| Skill | Description | Tokens |
|-------|-------------|--------|
| ⚡ [**NeuralVaultSkill**](https://github.com/getobyte/NeuralVaultSkill) | The "Daily Driver" — teaches agents to save context autonomously and use token-saving tools | ~383 |
| 🧹 [**NeuralVaultArchivist**](https://github.com/getobyte/NeuralVaultArchivist) | The "Maintenance Tool" — merges overlapping memories into Master Records without deleting data | on-demand |

---

## 💡 Why Low-Token Matters

Typical MCP servers waste thousands of tokens on emojis and full content dumps.  
**NeuralVaultCore reduces overhead by up to 7×** using smart truncation and pipe-delimited ASCII output.

---

## 🚀 Installation

Choose the setup method that fits your workflow:

### Option 1 — Installer Wizard *(Recommended)*

```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
python install.py
```

> The wizard handles venv, dependencies, search model, and MCP config automatically.

---

### Option 2 — Manual Setup

```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
python -m venv venv

# Activate the virtual environment:
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows

pip install -e ".[full]"
nvc init
nvc print-config --client claude-code
```

---

### Option 3 — Docker *(Homelab / LAN Access)*

**Step 1** — Clone and configure:
```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
cp .env.example .env
```

**Step 2** — Generate an API key and paste it in `.env` at `NVC_API_KEY`:
```bash
python -c "import secrets; print('nvc_' + secrets.token_hex(24))"
```

**Step 3** — Start the containers:
```bash
docker compose up -d
```

**Step 4** — Find the server's IP address:
```bash
# Linux
ip addr | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr "IPv4"

# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1
```

---

## 🔗 Connecting to Your IDE

### Local Setup (Options 1 & 2)

Generate your config automatically:
```bash
nvc print-config --client cursor
nvc print-config --client claude-code
```

### Remote / Docker Setup (Option 3)

Add this to your MCP config (e.g., `~/.claude.json`):

```json
{
  "mcpServers": {
    "neural-vault-core": {
      "url": "http://<YOUR_SERVER_IP>:9998/sse",
      "headers": {
        "Authorization": "Bearer nvc_YOUR_GENERATED_KEY"
      }
    }
  }
}
```

---

## 🛠️ CLI Commands Reference

### Core

```bash
nvc store <key> <content> [--tags t1,t2] [--ns default]
nvc get <key> [--ns default]
nvc search <query> [--ns ...]
nvc list [--limit 50] [--keys_only]
nvc stats
```

### Workflow

```bash
nvc checkpoint <namespace> <content>

# Example:
nvc checkpoint project:myapp "Finished auth refactor."
```

### Maintenance

```bash
nvc doctor      # Diagnostic checks
nvc repair      # DB maintenance
nvc dashboard   # Launch Web UI → http://localhost:9999
```

---

## 🏗️ Architecture

```
NeuralVaultCore/
├── core/         # Business logic (storage, auth, importers, doctor)
├── hooks/        # Shell / systemd integration scripts
├── NVC-BaseUI/   # React 19 + TypeScript + Tailwind 4 + shadcn
└── server.py     # MCP server entry point (stdio / sse)
```

---

## 🔒 Security

| Area | Details |
|------|---------|
| **API Keys** | `nvc_` prefix, constant-time comparison |
| **Auth** | Bearer token required for remote/homelab setups |
| **Privacy** | Zero telemetry, zero cloud — fully local-first |

---

## 📦 Storage Limits

| Field | Limit |
|-------|-------|
| Key | 256 chars |
| Title | 512 chars |
| Content | 1 MB |
| Versions | 5 |

---

<div align="center">

**NeuralVaultCore v1.0** — Cyber-Draco Legacy  
Built with ❤️ by [getobyte](https://github.com/getobyte)

</div>
