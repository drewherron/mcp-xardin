from typing import Optional

from xardin.server import mcp
from xardin.db import get_connection
from xardin.db.queries import (
    find_plant, search_plants,
    find_planting, search_plantings,
    resolve_location, add_adjacency,
)


@mcp.tool()
def add_location(name: str, description: Optional[str] = None) -> str:
    """Add a new garden location (e.g. 'raised bed', 'porch containers')."""
    conn = get_connection()

    existing = conn.execute(
        "SELECT id FROM locations WHERE name = ? COLLATE NOCASE AND active = 1", (name,)
    ).fetchone()
    if existing:
        return f"Location '{name}' already exists (id={existing['id']})"

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
    notes: free-form spatial context — use for position relative to landmarks
           ("by the front door", "against the north fence"), soil type, etc.
           Prefer notes over creating a new location for descriptors like these.
           The locations table is for ground or other soil containers.
    adjacent_to: location names near this one (additive; links are not removed)
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name FROM locations WHERE name = ? COLLATE NOCASE AND active = 1",
        (location,),
    ).fetchone()
    if not row:
        return f"No active location found matching '{location}'"

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
                "SELECT id, name FROM locations WHERE name = ? COLLATE NOCASE AND active = 1",
                (name,),
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
    species: Optional[str] = None,
    variety: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Register a plant type (species, variety). Call add_planting separately
    for each location where it's growing.
    """
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO plants (name, species, variety, notes) VALUES (?, ?, ?, ?)",
        (name, species, variety, notes),
    )
    conn.commit()
    return f"Added plant '{name}' (id={cursor.lastrowid})"


@mcp.tool()
def add_planting(
    plant: str,
    location: Optional[str] = None,
    quantity: Optional[int] = None,
    date_planted: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Record a group of plants growing in a specific location.

    Call add_plant first if this plant type isn't in the database yet.
    quantity: number of individual plants in this group, if known

    For seeds purchased but not yet started, add_plant alone is sufficient —
    only call add_planting once there's a specific growing location.

    Before passing a location string, read garden://locations and check whether
    the intended location already exists under a different name or description.
    Locations often have no fixed name and may be referred to differently each
    time (e.g. "Jane's window", "the bedroom window", "under the front
    bedroom window" may all refer to the same row). Use the existing name if
    there's a clear match; only treat it as new if no existing location fits.
    """
    conn = get_connection()
    plant_row = find_plant(conn, plant)
    if not plant_row:
        matches = search_plants(conn, plant)
        if matches:
            names = ", ".join(m["name"] for m in matches)
            return f"Ambiguous: '{plant}' matches multiple plants: {names}"
        return f"No plant found matching '{plant}' — call add_plant first"

    location_id = resolve_location(conn, location) if location else None

    cursor = conn.execute(
        """INSERT INTO plantings (plant_id, location_id, quantity, date_planted, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (plant_row["id"], location_id, quantity, date_planted, notes),
    )
    conn.commit()

    result = f"Added planting of '{plant_row['name']}' (id={cursor.lastrowid})"
    if location:
        result += f" in {location}"
    if quantity:
        result += f" ({quantity} plants)"
    return result


@mcp.tool()
def update_planting(
    plant: str,
    location: Optional[str] = None,
    active: Optional[bool] = None,
    quantity: Optional[int] = None,
    date_planted: Optional[str] = None,
    date_removed: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Update a specific planting's status, quantity, or dates.

    If a plant has multiple active plantings in different locations, provide
    location to identify which one.
    Set active=false when plants are removed, die, or are fully harvested.
    """
    conn = get_connection()
    planting = find_planting(conn, plant, location)
    if not planting:
        active_plantings = search_plantings(conn, plant)
        if len(active_plantings) > 1:
            locs = ", ".join(
                conn.execute("SELECT name FROM locations WHERE id = ?", (p["location_id"],))
                .fetchone()["name"]
                for p in active_plantings
                if p["location_id"]
            )
            return f"Ambiguous: '{plant}' has multiple active plantings ({locs}) — provide location"
        return f"No active planting found for '{plant}'"

    updates = {}
    if active is not None:
        updates["active"] = 1 if active else 0
    if quantity is not None:
        updates["quantity"] = quantity
    if date_planted is not None:
        updates["date_planted"] = date_planted
    if date_removed is not None:
        updates["date_removed"] = date_removed
    if notes is not None:
        updates["notes"] = notes

    if not updates:
        return "Nothing to update"

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [planting["id"]]
    conn.execute(
        f"UPDATE plantings SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values,
    )
    conn.commit()

    changed = ", ".join(f"{k}={v}" for k, v in updates.items())
    plant_name = find_plant(conn, plant)["name"]
    return f"Updated planting of '{plant_name}': {changed}"


@mcp.tool()
def update_plant(
    plant: str,
    species: Optional[str] = None,
    variety: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Update a plant type's species, variety, or notes."""
    conn = get_connection()
    existing = find_plant(conn, plant)
    if not existing:
        matches = search_plants(conn, plant)
        if matches:
            names = ", ".join(m["name"] for m in matches)
            return f"Ambiguous: '{plant}' matches multiple plants: {names}"
        return f"No plant found matching '{plant}'"

    updates = {}
    if species is not None:
        updates["species"] = species
    if variety is not None:
        updates["variety"] = variety
    if notes is not None:
        updates["notes"] = notes

    if not updates:
        return "Nothing to update"

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
    """Get details and history for a plant type, including all its plantings."""
    conn = get_connection()
    existing = find_plant(conn, plant)
    if not existing:
        matches = search_plants(conn, plant)
        if matches:
            names = ", ".join(m["name"] for m in matches)
            return f"Ambiguous: '{plant}' matches multiple plants: {names}"
        return f"No plant found matching '{plant}'"

    lines = [f"# {existing['name']}"]
    if existing["species"]:
        lines.append(f"Species: {existing['species']}")
    if existing["variety"]:
        lines.append(f"Variety: {existing['variety']}")
    if existing["notes"]:
        lines.append(f"Notes: {existing['notes']}")

    # list all plantings
    plantings = conn.execute(
        """SELECT pt.id, pt.active, pt.quantity, pt.date_planted, pt.date_removed,
                  l.name as location
           FROM plantings pt
           LEFT JOIN locations l ON pt.location_id = l.id
           WHERE pt.plant_id = ?
           ORDER BY pt.active DESC, pt.date_planted""",
        (existing["id"],),
    ).fetchall()

    if plantings:
        lines.append("\n## Plantings")
        for pt in plantings:
            status = "active" if pt["active"] else "inactive"
            parts = [f"- [{status}]"]
            if pt["location"]:
                parts.append(pt["location"])
            if pt["quantity"]:
                parts.append(f"{pt['quantity']} plants")
            if pt["date_planted"]:
                parts.append(f"planted {pt['date_planted']}")
            if pt["date_removed"]:
                parts.append(f"removed {pt['date_removed']}")
            lines.append(" ".join(parts))

    # combined activity/observation timeline across all plantings
    activities = conn.execute(
        """SELECT a.activity_type as type, a.description, a.timestamp
           FROM activities a
           JOIN plantings pt ON a.planting_id = pt.id
           WHERE pt.plant_id = ?""",
        (existing["id"],),
    ).fetchall()
    observations = conn.execute(
        """SELECT 'observed' as type, o.observation as description,
                  o.possible_cause, o.timestamp
           FROM observations o
           JOIN plantings pt ON o.planting_id = pt.id
           WHERE pt.plant_id = ?""",
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
