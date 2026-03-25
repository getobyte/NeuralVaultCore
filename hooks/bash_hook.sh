#!/bin/bash
# NeuralVaultCore — Bash shell hook
# Add to ~/.bashrc: source /path/to/NeuralVaultCore/hooks/bash_hook.sh

_NVC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_NVC_LAST_CMD=""

_nvc_capture() {
    local cmd
    cmd="$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')"
    # Dedup: skip if same as last captured
    if [ "$cmd" = "$_NVC_LAST_CMD" ]; then
        return
    fi
    _NVC_LAST_CMD="$cmd"
    # Run in background to not slow down the terminal
    python3 "$_NVC_DIR/core/shell_capture.py" "$cmd" &>/dev/null &
}

# Append to PROMPT_COMMAND (don't overwrite)
if [[ "$PROMPT_COMMAND" != *"_nvc_capture"* ]]; then
    PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND;}_nvc_capture"
fi
