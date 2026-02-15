"""Shared query helpers used by multiple tool modules."""

from typing import Optional


def find_plant(conn, plant: str) -> Optional[dict]:
    """Find a plant by ID (if numeric) or case-insensitive name match.
    Falls back to partial match if no exact match found.
    Returns None if no match or if multiple partial matches (ambiguous).
    """
    if plant.isdigit():
        row = conn.execute("SELECT * FROM plants WHERE id = ?", (int(plant),)).fetchone()
        return dict(row) if row else None

    row = conn.execute(
        "SELECT * FROM plants WHERE name = ? COLLATE NOCASE", (plant,)
    ).fetchone()
    if row:
        return dict(row)

    # fall back to partial match
    matches = search_plants(conn, plant)
    return matches[0] if len(matches) == 1 else None


def search_plants(conn, query: str) -> list[dict]:
    """Partial name search — returns all active plants whose name contains query."""
    rows = conn.execute(
        "SELECT * FROM plants WHERE name LIKE ? COLLATE NOCASE AND active = 1",
        (f"%{query}%",),
    ).fetchall()
    return [dict(r) for r in rows]


def add_adjacency(conn, location_id: int, adjacent_id: int):
    """Create a symmetric adjacency link between two locations."""
    conn.execute(
        "INSERT OR IGNORE INTO location_adjacency (location_id, adjacent_id) VALUES (?, ?)",
        (location_id, adjacent_id),
    )
    conn.execute(
        "INSERT OR IGNORE INTO location_adjacency (location_id, adjacent_id) VALUES (?, ?)",
        (adjacent_id, location_id),
    )


def resolve_location(conn, location: str) -> int:
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
