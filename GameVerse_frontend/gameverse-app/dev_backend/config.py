"""Database settings, read from environment variables or a local .env file.

No password is ever hard-coded. Copy .env.example to .env and fill it in,
or export the GV_DB_* variables in your shell.
"""
import os
from dataclasses import dataclass
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _load_env_file(path: Path = _ENV_FILE) -> None:
    """Minimal .env loader (KEY=VALUE lines). Real env vars take priority."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    schema: str


def load_config() -> DbConfig:
    _load_env_file()
    return DbConfig(
        host=os.environ.get("GV_DB_HOST", "localhost"),
        port=int(os.environ.get("GV_DB_PORT", "5432")),
        dbname=os.environ.get("GV_DB_NAME", "postgres"),
        user=os.environ.get("GV_DB_USER", "postgres"),
        password=os.environ.get("GV_DB_PASSWORD", ""),
        schema=os.environ.get("GV_DB_SCHEMA", "gameverse"),
    )
