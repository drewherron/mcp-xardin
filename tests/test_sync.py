import re
import tempfile
import os

from xardin.ingestion.sync import check_entry, content_hash, record_sync
from xardin.tools.sync_notes import sync_notes, mark_synced


def extract_sync_tokens(result: str) -> dict:
    """Parse org_timestamp → sync_token pairs from sync_notes output."""
    tokens = {}
    for m in re.finditer(r"\[([^\]]+)\].*?\n\s*sync_token: (\S+)", result, re.DOTALL):
        tokens[m.group(1)] = m.group(2)
    return tokens


def test_new_entry(db):
    status = check_entry(db, "2026-02-10 Tue 14:32", "some content")
    assert status == "new"


def test_unchanged_entry(db):
    record_sync(db, "2026-02-10 Tue 14:32", content_hash("some content"))
    db.commit()
    status = check_entry(db, "2026-02-10 Tue 14:32", "some content")
    assert status == "unchanged"


def test_updated_entry(db):
    record_sync(db, "2026-02-10 Tue 14:32", content_hash("original content"))
    db.commit()
    status = check_entry(db, "2026-02-10 Tue 14:32", "edited content")
    assert status == "updated"


SAMPLE_ORG = """\
* Planted tomatoes
  <2026-02-10 Tue 14:32>

* Watered everything
  <2026-02-11 Wed 09:00>
"""


def test_sync_notes_finds_new_entries(db):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".org", delete=False) as f:
        f.write(SAMPLE_ORG)
        f.flush()
        result = sync_notes(f.name)
    os.unlink(f.name)

    assert "2 new entries" in result
    assert "Planted tomatoes" in result


def test_sync_notes_includes_sync_token(db):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".org", delete=False) as f:
        f.write(SAMPLE_ORG)
        f.flush()
        result = sync_notes(f.name)
    os.unlink(f.name)

    assert "sync_token:" in result


def test_sync_notes_idempotent_after_mark_synced(db):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".org", delete=False) as f:
        f.write(SAMPLE_ORG)
        path = f.name

    try:
        result = sync_notes(path)
        assert "2 new entries" in result

        tokens = extract_sync_tokens(result)
        for ts, token in tokens.items():
            mark_synced(ts, token)

        result2 = sync_notes(path)
        assert "No new or updated" in result2
    finally:
        os.unlink(path)


def test_sync_notes_unconfirmed_entries_reappear(db):
    # entries that were returned but never mark_synced should come back next run
    with tempfile.NamedTemporaryFile(mode="w", suffix=".org", delete=False) as f:
        f.write(SAMPLE_ORG)
        path = f.name

    try:
        result = sync_notes(path)
        tokens = extract_sync_tokens(result)

        # LLM processes only the first entry
        ts = "2026-02-10 Tue 14:32"
        mark_synced(ts, tokens[ts])

        result2 = sync_notes(path)
        assert "Watered everything" in result2
        assert "2026-02-10 Tue 14:32" not in result2
    finally:
        os.unlink(path)
