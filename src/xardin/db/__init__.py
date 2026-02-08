import sqlite3
from pathlib import Path

from xardin.config import DB_PATH
from .schema import init_db

# single connection reused for the lifetime of the server
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is not None:
        return _connection

    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    _connection = sqlite3.connect(str(db_path))
    _connection.execute("PRAGMA journal_mode=WAL")  # better read concurrency
    _connection.execute("PRAGMA foreign_keys=ON")   # sqlite doesn't enforce FKs by default
    _connection.row_factory = sqlite3.Row

    init_db(_connection)
    return _connection
