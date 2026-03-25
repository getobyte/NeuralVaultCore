#!/bin/zsh
# NeuralVaultCore — Zsh shell hook
# Add to ~/.zshrc: source /path/to/NeuralVaultCore/hooks/zsh_hook.sh

_NVC_DIR="${0:A:h}/.."
_NVC_LAST_CMD=""

_nvc_preexec() {
    _NVC_PENDING_CMD="$1"
}

_nvc_precmd() {
    if [ -n "$_NVC_PENDING_CMD" ] && [ "$_NVC_PENDING_CMD" != "$_NVC_LAST_CMD" ]; then
        _NVC_LAST_CMD="$_NVC_PENDING_CMD"
        python3 "$_NVC_DIR/core/shell_capture.py" "$_NVC_PENDING_CMD" &>/dev/null &
    fi
    _NVC_PENDING_CMD=""
}

autoload -Uz add-zsh-hook
add-zsh-hook preexec _nvc_preexec
add-zsh-hook precmd _nvc_precmd
