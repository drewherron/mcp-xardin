from xardin.server import mcp
from xardin.db import get_connection
from xardin.db.schema import SCHEMA


@mcp.resource("garden://schema")
def get_schema() -> str:
    """The database schema DDL. Useful for generating SQL queries."""
    return SCHEMA


@mcp.resource("garden://plants")
def get_plants() -> str:
    """Summary of all active plants in the garden."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.name, p.date_planted, p.species, p.variety,
                  l.name as location
           FROM plants p
           LEFT JOIN locations l ON p.location_id = l.id
           WHERE p.active = 1
           ORDER BY p.date_planted"""
    ).fetchall()

    if not rows:
        return "No active plants."

    lines = []
    for r in rows:
        parts = [r["name"]]
        if r["variety"]:
            parts[0] += f" ({r['variety']})"
        if r["location"]:
            parts.append(f"in {r['location']}")
        if r["date_planted"]:
            parts.append(f"planted {r['date_planted']}")
        lines.append(" — ".join(parts))

    return "\n".join(lines)


@mcp.resource("garden://locations")
def get_locations() -> str:
    """All garden locations and what's currently planted in each."""
    conn = get_connection()
    locations = conn.execute(
        "SELECT id, name, description FROM locations ORDER BY name"
    ).fetchall()

    if not locations:
        return "No locations defined."

    lines = []
    for loc in locations:
        header = loc["name"]
        if loc["description"]:
            header += f" — {loc['description']}"
        lines.append(header)

        plants = conn.execute(
            "SELECT name FROM plants WHERE location_id = ? AND active = 1",
            (loc["id"],),
        ).fetchall()
        if plants:
            for p in plants:
                lines.append(f"  - {p['name']}")
        else:
            lines.append("  (empty)")
        lines.append("")

    return "\n".join(lines).strip()


@mcp.resource("garden://recent-activity")
def get_recent_activity() -> str:
    """Last 30 activities and observations, most recent first."""
    conn = get_connection()

    # pull from both tables and interleave by timestamp
    activities = conn.execute(
        """SELECT activity_type as type, a.description, a.timestamp,
                  p.name as plant, l.name as location
           FROM activities a
           LEFT JOIN plants p ON a.plant_id = p.id
           LEFT JOIN locations l ON a.location_id = l.id
           ORDER BY timestamp DESC LIMIT 30"""
    ).fetchall()

    observations = conn.execute(
        """SELECT 'observed' as type, observation as description, timestamp,
                  p.name as plant, l.name as location
           FROM observations o
           LEFT JOIN plants p ON o.plant_id = p.id
           LEFT JOIN locations l ON o.location_id = l.id
           ORDER BY timestamp DESC LIMIT 30"""
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
