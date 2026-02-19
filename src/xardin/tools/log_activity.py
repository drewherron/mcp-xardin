from datetime import datetime
from typing import Optional

from xardin.server import mcp
from xardin.db import get_connection
from xardin.db.queries import find_planting, search_plantings, resolve_location


@mcp.tool()
def log_activity(
    activity_type: str,
    description: str,
    plant: Optional[str] = None,
    location: Optional[str] = None,
    timestamp: Optional[str] = None,
    quantity: Optional[str] = None,
    possible_cause: Optional[str] = None,
    source: str = "direct_log",
) -> str:
    """Log a garden activity or observation.

    activity_type should be one of: planted, fertilized, pruned,
    harvested, moved, observed, treated, other.

    Use 'observed' for observations (e.g. wilting, pests, flowering).
    possible_cause is only relevant for 'observed' entries.
    Set source to 'org_sync' when logging from sync_notes output.

    quantity: free-text harvest or activity amount, e.g. '3 lbs' or '6 heads'.
              This is not a plant count — use add_planting for that.
    timestamp: ISO 8601 datetime string; defaults to now if omitted.

    If a plant has multiple active plantings in different locations, provide
    location to identify which one. If the activity implies a planting is
    finished (died, pulled out, or final harvest of a once-and-done crop),
    also call update_planting with active=false for that planting.
    """
    conn = get_connection()
    ts = timestamp or datetime.now().isoformat()

    planting_id = None
    location_id = None
    ambiguous = False

    if plant:
        planting = find_planting(conn, plant, location)
        if planting:
            planting_id = planting["id"]
            location_id = planting["location_id"]
        elif search_plantings(conn, plant):
            ambiguous = True
    elif location:
        location_id = resolve_location(conn, location)

    if activity_type == "observed":
        conn.execute(
            """INSERT INTO observations
               (planting_id, location_id, observation, possible_cause, timestamp, source)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (planting_id, location_id, description, possible_cause, ts, source),
        )
    else:
        conn.execute(
            """INSERT INTO activities
               (planting_id, location_id, activity_type, description, quantity, timestamp, source)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (planting_id, location_id, activity_type, description, quantity, ts, source),
        )

    conn.commit()

    result = f"Logged {activity_type}: {description}"
    if plant:
        result += f" ({plant})"
    if ambiguous:
        result += (
            f" — note: '{plant}' has multiple active plantings, logged without planting link;"
            " provide location to link to a specific planting"
        )
    return result


@mcp.tool()
def log_activities(entries: list[dict]) -> str:
    """Log multiple activities at once. Each entry should have the same
    fields as log_activity: activity_type, description, and optionally
    plant, location, timestamp, quantity, possible_cause, source.
    """
    results = []
    for entry in entries:
        try:
            r = log_activity(**entry)
            results.append(r)
        except Exception as e:
            desc = entry.get("description", "?")
            results.append(f"Error logging '{desc}': {e}")

    return f"Logged {len(results)} entries:\n" + "\n".join(results)
