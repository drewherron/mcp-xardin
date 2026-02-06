from typing import Optional

from xardin.server import mcp
from xardin.db import get_connection


@mcp.tool()
def add_location(name: str, description: Optional[str] = None) -> str:
    """Add a new garden location (e.g. 'raised bed', 'porch containers')."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO locations (name, description) VALUES (?, ?)",
        (name, description),
    )
    conn.commit()
    return f"Added location '{name}' (id={cursor.lastrowid})"
