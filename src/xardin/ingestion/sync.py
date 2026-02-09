"""Track which org entries have been synced to avoid duplicates."""

import hashlib


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def check_entry(conn, timestamp: str, raw: str) -> str:
    """Check an org entry against the sync log.

    Returns 'new', 'unchanged', or 'updated'.
    """
    row = conn.execute(
        "SELECT content_hash FROM sync_log WHERE org_timestamp = ?", (timestamp,)
    ).fetchone()

    if row is None:
        return "new"

    if row["content_hash"] == content_hash(raw):
        return "unchanged"

    return "updated"


def record_sync(conn, timestamp: str, raw: str, status: str = "success"):
    """Insert or update the sync log for an entry."""
    h = content_hash(raw)
    existing = conn.execute(
        "SELECT id FROM sync_log WHERE org_timestamp = ?", (timestamp,)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE sync_log SET content_hash = ?, synced_at = CURRENT_TIMESTAMP, status = ? WHERE id = ?",
            (h, status, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO sync_log (org_timestamp, content_hash, status) VALUES (?, ?, ?)",
            (timestamp, h, status),
        )
