from xardin.server import mcp
from xardin.db import get_connection
from xardin.ingestion.org_parser import parse_org_file
from xardin.ingestion.sync import check_entry, record_sync


@mcp.tool()
def sync_notes(file_path: str) -> str:
    """Sync garden notes from an org-mode file.

    Parses the file and returns any new or updated entries. The AI client
    should interpret each entry (identify plants, activities, locations)
    and call log_activity for each one.
    """
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

        record_sync(conn, entry.timestamp, entry.raw)

        item = f"[{entry.timestamp}] {entry.heading}"
        if entry.body:
            item += f"\n  {entry.body}"

        if status == "new":
            new_entries.append(item)
        else:
            updated_entries.append(item)

    conn.commit()

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

    parts.append("\n\nPlease interpret these entries and call log_activity for each one.")
    return "\n".join(parts)
