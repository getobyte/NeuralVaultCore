================================================================================
# NeuralVaultCore v1.0
================================================================================
Infinite Long-Term Memory for AI Agents — local, private, low-token.

NeuralVaultCore is an MCP memory server built for token efficiency. Any AI agent 
with MCP support (Claude Code, Cursor, OpenCode, Ollama) gets persistent memory 
across sessions. Single-user, local-first — your data never leaves your machine.

Author: getobyte | License: MIT | Python 3.10+ | MCP Compliant

--------------------------------------------------------------------------------
## 🤖 Official AI Agent Skills (Ecosystem)
--------------------------------------------------------------------------------

An MCP server is only as good as the AI using it. To get the absolute best 
performance, zero context bloat, and perfect autonomy, use these prompts:

* ⚡ NeuralVaultSkill: The "Daily Driver". Ultra-compact (~383 tokens). 
  Teaches agents to save context autonomously and use token-saving tools.
  URL: https://github.com/getobyte/NeuralVaultSkill

* 🧹 NeuralVaultArchivist: The "Maintenance Tool". On-demand consolidation. 
  Merges overlapping memories into Master Records without deleting data.
  URL: https://github.com/getobyte/NeuralVaultArchivist

--------------------------------------------------------------------------------
## Why Low-Token Matters
--------------------------------------------------------------------------------

Typical MCP servers waste thousands of tokens on emojis and full content dumps. 
NeuralVaultCore reduces overhead by up to 7x using smart truncation and 
pipe-delimited ASCII output.

--------------------------------------------------------------------------------
## Installation
--------------------------------------------------------------------------------

### Option 1: Installer Wizard (Recommended)

$ git clone https://github.com/getobyte/NeuralVaultCore.git
$ cd NeuralVaultCore
$ python install.py

(The wizard handles venv, dependencies, search model, and MCP config)

### Option 2: Manual Setup

$ git clone https://github.com/getobyte/NeuralVaultCore.git
$ cd NeuralVaultCore
$ python -m venv venv
$ source venv/bin/activate  # For Linux/macOS
$ venv\Scripts\activate     # For Windows
$ pip install -e ".[full]"
$ nvc init
$ nvc print-config --client claude-code

### Option 3: Docker (Homelab / LAN Access)

Step 1 — Clone and configure:
$ git clone https://github.com/getobyte/NeuralVaultCore.git
$ cd NeuralVaultCore
$ cp .env.example .env

Step 2 — Generate API key:
$ python -c "import secrets; print('nvc_' + secrets.token_hex(24))"

(Paste the key in your .env file at NVC_API_KEY)

Step 3 — Start the containers:
$ docker compose up -d

Step 4 — Find the server's IP address:
Linux:   ip addr | grep "inet " | grep -v 127.0.0.1
Windows: ipconfig | findstr "IPv4"
macOS:   ifconfig | grep "inet " | grep -v 127.0.0.1

--------------------------------------------------------------------------------
## 🔗 Connecting to Your IDE
--------------------------------------------------------------------------------

### Local Setup (Options 1 & 2)
Generate your config automatically:
$ nvc print-config --client cursor
$ nvc print-config --client claude-code

### Remote/Docker Setup (Option 3)
Add this to your MCP config (e.g., ~/.claude.json):

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

--------------------------------------------------------------------------------
## CLI Commands Reference
--------------------------------------------------------------------------------

CORE:
$ nvc store <key> <content> [--tags t1,t2] [--ns default]
$ nvc get <key> [--ns default]
$ nvc search <query> [--ns ...]
$ nvc list [--limit 50] [--keys_only]
$ nvc stats

WORKFLOW:
$ nvc checkpoint <namespace> <content>
Example: $ nvc checkpoint project:myapp "Finished auth refactor."

MAINTENANCE:
$ nvc doctor       # Diagnostic checks
$ nvc repair       # DB maintenance
$ nvc dashboard    # Launch Web UI (http://localhost:9999)

--------------------------------------------------------------------------------
## Architecture & Security
--------------------------------------------------------------------------------

FOLDER STRUCTURE:
- core/        : Business logic (storage, auth, importers, doctor)
- hooks/       : Shell/systemd integration scripts
- NVC-BaseUI/  : React 19 + TypeScript + Tailwind 4 + shadcn
- server.py    : MCP server entry point (stdio/sse)

SECURITY:
- API Keys: nvc_ prefix, constant-time comparison
- Auth: Required for remote-homelab (Bearer token)
- local-first: Zero telemetry, zero cloud. Your data stays on-prem

STORAGE LIMITS:
- Key: 256 chars | Title: 512 chars | Content: 1 MB | Versions: 5

================================================================================
NeuralVaultCore v1.0 — Cyber-Draco Legacy | built by getobyte
================================================================================
