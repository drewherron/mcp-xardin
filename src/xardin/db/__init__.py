import os
import sqlite3
from pathlib import Path

from .schema import init_db

DEFAULT_DB_PATH = os.path.join("data", "garden.db")

_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is not None:
        return _connection

    db_path = Path(os.environ.get("GARDEN_DB_PATH", DEFAULT_DB_PATH))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    _connection = sqlite3.connect(str(db_path))
    _connection.execute("PRAGMA journal_mode=WAL")
    _connection.execute("PRAGMA foreign_keys=ON")
    _connection.row_factory = sqlite3.Row

    init_db(_connection)
    return _connection
