from core.exceptions import NVCError, NVCAuthError, StorageError, ValidationError

__all__ = ["NVCError", "NVCAuthError", "StorageError", "ValidationError", "get_default_config", "get_default_storage"]


def get_default_config():
    """Load NVCConfig from .env in the project root (or env vars)."""
    from pathlib import Path
    from core.config import NVCConfig
    env_file = Path(__file__).parent.parent / ".env"
    return NVCConfig.from_env(env_file if env_file.exists() else None)


def get_default_storage():
    """Create SQLiteStorage with default config. Convenience factory."""
    from core.storage import SQLiteStorage
    return SQLiteStorage(get_default_config())
