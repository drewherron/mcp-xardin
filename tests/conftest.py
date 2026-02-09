import sqlite3
import pytest

import xardin.db
from xardin.db.schema import init_db


@pytest.fixture(autouse=True)
def db():
    """Provide a fresh in-memory database for each test."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    # patch the singleton so get_connection() returns our test db
    xardin.db._connection = conn
    yield conn
    conn.close()
    xardin.db._connection = None
