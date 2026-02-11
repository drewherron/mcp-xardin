"""Shared query helpers used by multiple tool modules."""

from typing import Optional


def find_plant(conn, plant: str) -> Optional[dict]:
    """Find a plant by ID (if numeric) or case-insensitive name match."""
    if plant.isdigit():
        row = conn.execute("SELECT * FROM plants WHERE id = ?", (int(plant),)).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM plants WHERE name = ? COLLATE NOCASE", (plant,)
        ).fetchone()
    return dict(row) if row else None


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
