import os

from xardin.server import mcp
from xardin.db import get_connection
from xardin.ingestion.org_parser import parse_org_file
from xardin.ingestion.sync import check_entry, content_hash, record_sync


@mcp.tool()
def sync_notes(file_path: str) -> str:
    """Sync garden notes from an org-mode file.

    Parses the file and returns any new or updated entries. The AI client
    should interpret each entry: registering new plants with add_plant,
    creating plantings with add_planting, and logging events with
    log_activity. After processing each entry, call mark_synced with the
    entry's org_timestamp and sync_token to confirm it was handled.
    Detailed instructions are included in the return value.
    """
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"

    conn = get_connection()
    entries = parse_org_file(file_path)

    new_entries = []
    updated_entries = []
    skipped = 0

    for entry in entries:
        if not entry.timestamp:
            continue  # skip entries without timestamps

        status = check_entry(conn, entry.timestamp, entry.raw)

        if status == "unchanged":
            skipped += 1
            continue

        token = content_hash(entry.raw)
        item = f"[{entry.timestamp}] {entry.heading}"
        if entry.body:
            item += f"\n  {entry.body}"
        item += f"\n  sync_token: {token}"

        if status == "new":
            new_entries.append(item)
        else:
            updated_entries.append(item)

    # build the response
    parts = []

    if new_entries:
        parts.append(f"## {len(new_entries)} new entries\n")
        parts.append("\n\n".join(new_entries))

    if updated_entries:
        parts.append(f"\n\n## {len(updated_entries)} updated entries\n")
        parts.append("\n\n".join(updated_entries))

    if skipped:
        parts.append(f"\n\n({skipped} unchanged entries skipped)")

    if not new_entries and not updated_entries:
        return "No new or updated entries found."

    parts.append(
        "\n\nPlease interpret these entries using the following steps:\n\n"
        "1. Read garden://locations and garden://plants before processing any entry. "
        "Use this to resolve location and plant references in the notes — do not pass "
        "raw location strings directly to add_planting without first checking whether "
        "an existing location matches. Locations may be referred to differently each "
        "time (e.g. 'the bedroom window', 'Jane's window', 'under the front "
        "bedroom' may all refer to the same location). Use the existing name when "
        "there is a clear match; only create a new location if none fits.\n\n"
        "2. For any plants not already in the database, call add_plant first "
        "(including species and variety if mentioned).\n\n"
        "3. Call add_planting for each location group (with quantity if known).\n\n"
        "4. Call log_activity (or log_activities) for each entry, setting "
        "source='org_sync'.\n\n"
        "5. If any entries indicate that plants were removed, pulled out, died, or "
        "were fully harvested (once-and-done crops like carrots or garlic), call "
        "update_planting with active=false for those plantings.\n\n"
        "6. After processing each entry, call mark_synced with the entry's "
        "org_timestamp and sync_token so it won't be returned again on the next sync."
    )
    return "\n".join(parts)


@mcp.tool()
def mark_synced(org_timestamp: str, sync_token: str) -> str:
    """Mark an org entry as processed after interpreting it from sync_notes output.

    Call this once per entry after all add_plant, add_planting, and
    log_activity calls for that entry are complete. Use the org_timestamp
    and sync_token values returned by sync_notes. Set source='org_sync'
    on any log_activity calls for this entry before calling mark_synced.
    """
    conn = get_connection()
    record_sync(conn, org_timestamp, sync_token)
    conn.commit()
    return f"Marked {org_timestamp} as synced."
