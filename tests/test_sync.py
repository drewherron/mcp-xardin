import tempfile
import os

from xardin.ingestion.sync import check_entry, record_sync
from xardin.tools.sync_notes import sync_notes


def test_new_entry(db):
    status = check_entry(db, "2026-02-10 Tue 14:32", "some content")
    assert status == "new"


def test_unchanged_entry(db):
    record_sync(db, "2026-02-10 Tue 14:32", "some content")
    db.commit()
    status = check_entry(db, "2026-02-10 Tue 14:32", "some content")
    assert status == "unchanged"


def test_updated_entry(db):
    record_sync(db, "2026-02-10 Tue 14:32", "original content")
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


def test_sync_notes_idempotent(db):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".org", delete=False) as f:
        f.write(SAMPLE_ORG)
        f.flush()
        sync_notes(f.name)
        result = sync_notes(f.name)
    os.unlink(f.name)

    assert "No new or updated" in result
