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
        """SELECT p.name, p.status, p.date_planted, p.species, p.variety,
                  l.name as location
           FROM plants p
           LEFT JOIN locations l ON p.location_id = l.id
           WHERE p.status = 'active'
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
