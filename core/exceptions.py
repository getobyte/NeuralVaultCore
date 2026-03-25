# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Custom exceptions
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════


class NVCError(Exception):
    """Base exception for NeuralVaultCore."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class NVCAuthError(NVCError):
    """Authentication or authorization failure."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class StorageError(NVCError):
    """Storage / database error."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class ValidationError(NVCError, ValueError):
    """Input validation error (also a ValueError for backward compatibility)."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
