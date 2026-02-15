from typing import Optional

from xardin.server import mcp
from xardin.db import get_connection
from xardin.db.queries import find_plant, search_plants, resolve_location, add_adjacency


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
def update_location(
    location: str,
    active: Optional[bool] = None,
    sun_exposure: Optional[str] = None,
    size: Optional[str] = None,
    notes: Optional[str] = None,
    adjacent_to: Optional[list[str]] = None,
) -> str:
    """Update a garden location's attributes or adjacency links.

    active: set to false to retire a location (hides it from the AI without
            deleting historical data)
    sun_exposure: e.g. 'full sun', 'partial shade', 'full shade'
    size: e.g. '4x8 ft'
    notes: free-form spatial or soil notes
    adjacent_to: location names near this one (additive; links are not removed)
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name FROM locations WHERE name = ? COLLATE NOCASE", (location,)
    ).fetchone()
    if not row:
        return f"No location found matching '{location}'"

    loc_id = row["id"]
    loc_name = row["name"]
    changed = []

    updates = {}
    if active is not None:
        updates["active"] = 1 if active else 0
    if sun_exposure is not None:
        updates["sun_exposure"] = sun_exposure
    if size is not None:
        updates["size"] = size
    if notes is not None:
        updates["notes"] = notes

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [loc_id]
        conn.execute(f"UPDATE locations SET {set_clause} WHERE id = ?", values)
        changed.extend(f"{k}={v}" for k, v in updates.items())

    if adjacent_to:
        linked = []
        for name in adjacent_to:
            adj_row = conn.execute(
                "SELECT id, name FROM locations WHERE name = ? COLLATE NOCASE", (name,)
            ).fetchone()
            if adj_row:
                add_adjacency(conn, loc_id, adj_row["id"])
                linked.append(adj_row["name"])
            else:
                cursor = conn.execute("INSERT INTO locations (name) VALUES (?)", (name,))
                add_adjacency(conn, loc_id, cursor.lastrowid)
                linked.append(name)
        changed.append(f"adjacent_to=[{', '.join(linked)}]")

    if not changed:
        return "Nothing to update"

    conn.commit()
    return f"Updated '{loc_name}': {', '.join(changed)}"


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
        """INSERT INTO plants (name, species, variety, date_planted, location_id, active)
           VALUES (?, ?, ?, ?, ?, 1)""",
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
    active: Optional[bool] = None,
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
        matches = search_plants(conn, plant)
        if matches:
            names = ", ".join(m["name"] for m in matches)
            return f"Ambiguous: '{plant}' matches multiple plants: {names}"
        return f"No plant found matching '{plant}'"

    updates = {}
    if active is not None:
        updates["active"] = 1 if active else 0
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
        matches = search_plants(conn, plant)
        if matches:
            names = ", ".join(m["name"] for m in matches)
            return f"Ambiguous: '{plant}' matches multiple plants: {names}"
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
    lines.append(f"Active: {bool(existing['active'])}")
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

    # combined timeline from both tables
    activities = conn.execute(
        """SELECT activity_type as type, description, timestamp
           FROM activities WHERE plant_id = ?""",
        (existing["id"],),
    ).fetchall()
    observations = conn.execute(
        """SELECT 'observed' as type, observation as description,
                  possible_cause, timestamp
           FROM observations WHERE plant_id = ?""",
        (existing["id"],),
    ).fetchall()

    history = sorted(
        [dict(r) for r in activities] + [dict(r) for r in observations],
        key=lambda r: r["timestamp"],
        reverse=True,
    )[:30]

    if history:
        lines.append("\n## History")
        for h in history:
            line = f"- [{h['timestamp']}] {h['type']}: {h['description']}"
            cause = h.get("possible_cause")
            if cause:
                line += f" (possible cause: {cause})"
            lines.append(line)

    return "\n".join(lines)
