from xardin.server import mcp
from xardin.db import get_connection
from xardin.db.schema import SCHEMA
from xardin.config import GROWING_ZONE, REGION


@mcp.resource("garden://context")
def get_context() -> str:
    """Static garden configuration: growing zone and region."""
    lines = [f"Growing zone: {GROWING_ZONE}"]
    if REGION:
        lines.append(f"Region: {REGION}")
    return "\n".join(lines)


@mcp.resource("garden://schema")
def get_schema() -> str:
    """The database schema DDL. Useful for generating SQL queries."""
    return SCHEMA


@mcp.resource("garden://plants")
def get_plants() -> str:
    """All registered plant types with active planting details. Plants with no active
    plantings are listed as catalog entries (e.g. seeds purchased but not yet started)."""
    conn = get_connection()

    plants = conn.execute(
        "SELECT id, name, species, variety FROM plants ORDER BY name"
    ).fetchall()

    if not plants:
        return "No plants registered."

    lines = []
    for p in plants:
        header = p["name"]
        if p["variety"]:
            header += f" ({p['variety']})"
        elif p["species"]:
            header += f" ({p['species']})"
        lines.append(header)

        plantings = conn.execute(
            """SELECT pt.quantity, pt.date_planted, l.name as location
               FROM plantings pt
               LEFT JOIN locations l ON pt.location_id = l.id
               WHERE pt.plant_id = ? AND pt.active = 1
               ORDER BY pt.date_planted""",
            (p["id"],),
        ).fetchall()

        if plantings:
            for pt in plantings:
                parts = [" -"]
                if pt["location"]:
                    parts.append(pt["location"])
                if pt["quantity"]:
                    parts.append(f"{pt['quantity']} plants")
                if pt["date_planted"]:
                    parts.append(f"planted {pt['date_planted']}")
                lines.append(" ".join(parts))
        else:
            lines.append("  (catalog only — not currently planted)")

        lines.append("")

    return "\n".join(lines).strip()


@mcp.resource("garden://locations")
def get_locations() -> str:
    """All garden locations and what's currently planted in each."""
    conn = get_connection()
    locations = conn.execute(
        "SELECT id, name, description, sun_exposure, size, notes FROM locations"
        " WHERE active = 1 ORDER BY name"
    ).fetchall()

    if not locations:
        return "No locations defined."

    lines = []
    for loc in locations:
        attrs = []
        if loc["sun_exposure"]:
            attrs.append(loc["sun_exposure"])
        if loc["size"]:
            attrs.append(loc["size"])
        header = loc["name"]
        if attrs:
            header += f" ({', '.join(attrs)})"
        if loc["description"]:
            header += f" — {loc['description']}"
        lines.append(header)

        if loc["notes"]:
            lines.append(f"  Notes: {loc['notes']}")

        adjacent = conn.execute(
            """SELECT l.name FROM locations l
               JOIN location_adjacency a ON l.id = a.adjacent_id
               WHERE a.location_id = ? AND l.active = 1
               ORDER BY l.name""",
            (loc["id"],),
        ).fetchall()
        if adjacent:
            lines.append(f"  Adjacent to: {', '.join(r['name'] for r in adjacent)}")

        plantings = conn.execute(
            """SELECT p.name, p.variety, pt.quantity
               FROM plantings pt
               JOIN plants p ON pt.plant_id = p.id
               WHERE pt.location_id = ? AND pt.active = 1""",
            (loc["id"],),
        ).fetchall()
        if plantings:
            for pt in plantings:
                entry = f"  - {pt['name']}"
                if pt["variety"]:
                    entry += f" ({pt['variety']})"
                if pt["quantity"]:
                    entry += f": {pt['quantity']} plants"
                lines.append(entry)
        else:
            lines.append("  (empty)")
        lines.append("")

    return "\n".join(lines).strip()


@mcp.resource("garden://recent-activity")
def get_recent_activity() -> str:
    """Last 30 activities and observations, most recent first."""
    conn = get_connection()

    activities = conn.execute(
        """SELECT a.activity_type as type, a.description, a.timestamp,
                  p.name as plant, l.name as location
           FROM activities a
           LEFT JOIN plantings pt ON a.planting_id = pt.id
           LEFT JOIN plants p ON pt.plant_id = p.id
           LEFT JOIN locations l ON a.location_id = l.id
           ORDER BY a.timestamp DESC LIMIT 30"""
    ).fetchall()

    observations = conn.execute(
        """SELECT 'observed' as type, o.observation as description, o.timestamp,
                  p.name as plant, l.name as location
           FROM observations o
           LEFT JOIN plantings pt ON o.planting_id = pt.id
           LEFT JOIN plants p ON pt.plant_id = p.id
           LEFT JOIN locations l ON o.location_id = l.id
           ORDER BY o.timestamp DESC LIMIT 30"""
    ).fetchall()

    combined = sorted(
        [dict(r) for r in activities] + [dict(r) for r in observations],
        key=lambda r: r["timestamp"],
        reverse=True,
    )[:30]

    if not combined:
        return "No recent activity."

    lines = []
    for r in combined:
        parts = [f"[{r['timestamp']}] {r['type']}: {r['description']}"]
        if r["plant"]:
            parts.append(r["plant"])
        if r["location"]:
            parts.append(f"in {r['location']}")
        lines.append(" — ".join(parts))

    return "\n".join(lines)
