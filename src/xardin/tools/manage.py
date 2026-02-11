from typing import Optional

from xardin.server import mcp
from xardin.db import get_connection
from xardin.db.queries import find_plant, resolve_location


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
    location_id = resolve_location(conn, location) if location else None

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


@mcp.tool()
def update_plant(
    plant: str,
    status: Optional[str] = None,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    species: Optional[str] = None,
    variety: Optional[str] = None,
    date_planted: Optional[str] = None,
    date_removed: Optional[str] = None,
) -> str:
    """Update an existing plant. Identify it by name or ID."""
    conn = get_connection()
    existing = find_plant(conn, plant)
    if not existing:
        return f"No plant found matching '{plant}'"

    updates = {}
    if status is not None:
        updates["status"] = status
    if location is not None:
        updates["location_id"] = resolve_location(conn, location)
    if notes is not None:
        updates["notes"] = notes
    if species is not None:
        updates["species"] = species
    if variety is not None:
        updates["variety"] = variety
    if date_planted is not None:
        updates["date_planted"] = date_planted
    if date_removed is not None:
        updates["date_removed"] = date_removed

    if not updates:
        return "Nothing to update"

    # SET clause can only come from our hardcoded keys, not user input
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [existing["id"]]
    conn.execute(
        f"UPDATE plants SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values,
    )
    conn.commit()

    changed = ", ".join(f"{k}={v}" for k, v in updates.items())
    return f"Updated '{existing['name']}': {changed}"


@mcp.tool()
def get_plant_info(plant: str) -> str:
    """Get details about a plant by name or ID."""
    conn = get_connection()
    existing = find_plant(conn, plant)
    if not existing:
        return f"No plant found matching '{plant}'"

    # resolve location name for display
    location_name = None
    if existing["location_id"]:
        loc = conn.execute(
            "SELECT name FROM locations WHERE id = ?", (existing["location_id"],)
        ).fetchone()
        if loc:
            location_name = loc["name"]

    lines = [f"# {existing['name']}"]
    lines.append(f"Status: {existing['status']}")
    if location_name:
        lines.append(f"Location: {location_name}")
    if existing["species"]:
        lines.append(f"Species: {existing['species']}")
    if existing["variety"]:
        lines.append(f"Variety: {existing['variety']}")
    if existing["date_planted"]:
        lines.append(f"Planted: {existing['date_planted']}")
    if existing["date_removed"]:
        lines.append(f"Removed: {existing['date_removed']}")
    if existing["notes"]:
        lines.append(f"Notes: {existing['notes']}")

    return "\n".join(lines)
