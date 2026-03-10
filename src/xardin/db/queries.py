"""Shared query helpers used by multiple tool modules."""

from typing import Optional


def find_plant(conn, plant: str) -> Optional[dict]:
    """Find a plant type by ID (if numeric) or case-insensitive name match.
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

    matches = search_plants(conn, plant)
    return matches[0] if len(matches) == 1 else None


def search_plants(conn, query: str) -> list[dict]:
    """Partial search — returns plant types whose name or type contains query."""
    rows = conn.execute(
        "SELECT * FROM plants WHERE name LIKE ? COLLATE NOCASE OR type LIKE ? COLLATE NOCASE",
        (f"%{query}%", f"%{query}%"),
    ).fetchall()
    return [dict(r) for r in rows]


def find_planting(conn, plant: str, location: str = None) -> Optional[dict]:
    """Find an active planting by plant name and optional location.

    If location is omitted, returns the single active planting if unambiguous.
    Returns None if the plant isn't found, the planting isn't found, or if
    multiple active plantings exist and no location was given.
    """
    plant_row = find_plant(conn, plant)
    if not plant_row:
        return None

    if location:
        loc = conn.execute(
            "SELECT id FROM locations WHERE name = ? COLLATE NOCASE AND active = 1",
            (location,),
        ).fetchone()
        if not loc:
            return None
        row = conn.execute(
            "SELECT * FROM plantings WHERE plant_id = ? AND location_id = ? AND active = 1",
            (plant_row["id"], loc["id"]),
        ).fetchone()
        return dict(row) if row else None

    rows = conn.execute(
        "SELECT * FROM plantings WHERE plant_id = ? AND active = 1",
        (plant_row["id"],),
    ).fetchall()
    return dict(rows[0]) if len(rows) == 1 else None


def search_plantings(conn, plant: str) -> list[dict]:
    """Return all active plantings for plants whose name contains query."""
    rows = conn.execute(
        """SELECT pt.* FROM plantings pt
           JOIN plants p ON pt.plant_id = p.id
           WHERE p.name LIKE ? COLLATE NOCASE AND pt.active = 1""",
        (f"%{plant}%",),
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


def resolve_location(conn, location: str) -> tuple[int, bool]:
    """Look up an active location by name, creating a new one if none exists.

    Returns (location_id, created) where created=True if a new location was inserted.
    """
    row = conn.execute(
        "SELECT id FROM locations WHERE name = ? COLLATE NOCASE AND active = 1", (location,)
    ).fetchone()
    if row:
        return row["id"], False
    cursor = conn.execute(
        "INSERT INTO locations (name) VALUES (?)", (location,)
    )
    return cursor.lastrowid, True
