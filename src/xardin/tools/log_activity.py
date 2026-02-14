from datetime import datetime
from typing import Optional

from xardin.server import mcp
from xardin.db import get_connection
from xardin.db.queries import find_plant, search_plants, resolve_location


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
    Set source to 'org_sync' when logging from sync_notes output.

    If the activity implies a plant is finished (died, pulled out, or
    final harvest of a once-and-done crop like carrots or garlic), also
    call update_plant with active=false for that plant.
    """
    conn = get_connection()
    ts = timestamp or datetime.now().isoformat()

    plant_id = None
    ambiguous = False
    if plant:
        existing = find_plant(conn, plant)
        if existing:
            plant_id = existing["id"]
        elif len(search_plants(conn, plant)) > 1:
            ambiguous = True

    location_id = None
    if location:
        location_id = resolve_location(conn, location)

    if activity_type == "observed":
        conn.execute(
            """INSERT INTO observations
               (plant_id, location_id, observation, possible_cause, timestamp, source)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (plant_id, location_id, description, possible_cause, ts, source),
        )
    else:
        conn.execute(
            """INSERT INTO activities
               (plant_id, location_id, activity_type, description, quantity, timestamp, source)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (plant_id, location_id, activity_type, description, quantity, ts, source),
        )

    conn.commit()

    result = f"Logged {activity_type}: {description}"
    if plant:
        result += f" ({plant})"
    if ambiguous:
        result += f" — note: '{plant}' matched multiple plants, logged without plant link"
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
