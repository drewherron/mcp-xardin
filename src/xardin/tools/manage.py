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


def _resolve_location(conn, location: str) -> int:
    """Look up a location by name, creating it if it doesn't exist."""
    row = conn.execute(
        "SELECT id FROM locations WHERE name = ? COLLATE NOCASE", (location,)
    ).fetchone()
    if row:
        return row["id"]
    cursor = conn.execute(
        "INSERT INTO locations (name) VALUES (?)", (location,)
    )
    return cursor.lastrowid


@mcp.tool()
def add_plant(
    name: str,
    location: Optional[str] = None,
    species: Optional[str] = None,
    variety: Optional[str] = None,
    date_planted: Optional[str] = None,
) -> str:
    """Add a new plant to the garden. Location is matched by name or created automatically."""
    conn = get_connection()
    location_id = _resolve_location(conn, location) if location else None

    cursor = conn.execute(
        """INSERT INTO plants (name, species, variety, date_planted, location_id, status)
           VALUES (?, ?, ?, ?, ?, 'active')""",
        (name, species, variety, date_planted, location_id),
    )
    conn.commit()

    result = f"Added plant '{name}' (id={cursor.lastrowid})"
    if location:
        result += f" in {location}"
    return result
