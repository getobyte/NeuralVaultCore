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

## 🤖 Ecosystem

NeuralVaultCore is one piece of a 3-part system. The server alone is not enough — pair it with the right prompts:

| Skill | Role | Tokens |
|-------|------|--------|
| ⚡ [**NeuralVaultSkill**](https://github.com/getobyte/NeuralVaultSkill) | Daily driver — autonomous background memory management | ~383 |
| 🧹 [**NeuralVaultArchivist**](https://github.com/getobyte/NeuralVaultArchivist) | Maintenance — merges overlapping memories into master records without deleting data | on-demand |

---

## 💡 Why Low-Token Matters

Most MCP servers waste thousands of tokens on verbose output.  
NeuralVaultCore cuts overhead by up to **7×** using smart truncation and pipe-delimited ASCII responses.

---

## 🚀 Installation

### Option 1 — Installer Wizard *(Recommended)*

```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
python install.py
```

The wizard handles venv, dependencies, search model, and MCP config automatically.

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

```bash
git clone https://github.com/getobyte/NeuralVaultCore.git
cd NeuralVaultCore
cp .env.example .env
```

Generate an API key and paste it into `.env` at `NVC_API_KEY`:
```bash
python -c "import secrets; print('nvc_' + secrets.token_hex(24))"
```

Start the containers:
```bash
docker compose up -d
```

Find your server IP:
```bash
ip addr | grep "inet " | grep -v 127.0.0.1   # Linux
ipconfig | findstr "IPv4"                      # Windows
ifconfig | grep "inet " | grep -v 127.0.0.1   # macOS
```

---

## 🔗 Connecting to Your IDE

### Local (Options 1 & 2)

```bash
nvc print-config --client cursor
nvc print-config --client claude-code
```

### Remote / Docker (Option 3)

Add to your MCP config (e.g. `~/.claude.json`):

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

## 🛠️ CLI Reference

```bash
# Core
nvc store <key> <content> [--tags t1,t2] [--ns default]
nvc get <key> [--ns default]
nvc search <query> [--ns ...]
nvc list [--limit 50] [--keys_only]
nvc stats

# Workflow
nvc checkpoint <namespace> <content>
# nvc checkpoint project:myapp "Finished auth refactor."

# Maintenance
nvc doctor      # Diagnostic checks
nvc repair      # DB maintenance
nvc dashboard   # Web UI → http://localhost:9999
```

---

## 🏗️ Architecture

```
NeuralVaultCore/
├── core/         # Storage, auth, importers, doctor
├── hooks/        # Shell / systemd integration
├── NVC-BaseUI/   # React 19 + TypeScript + Tailwind 4 + shadcn
└── server.py     # MCP entry point (stdio / sse)
```

---

## 🔒 Security

| Area | Details |
|------|---------|
| **API Keys** | `nvc_` prefix, constant-time comparison |
| **Auth** | Bearer token required for remote setups |
| **Privacy** | Zero telemetry, zero cloud, fully local |

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
