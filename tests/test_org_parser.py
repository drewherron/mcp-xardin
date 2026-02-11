from xardin.ingestion.org_parser import parse_org_text


SAMPLE = """\
* Planted tomatoes in the raised bed
  <2026-02-10 Tue 14:32>

* Moved the pepper to the sunny spot by the fence
  <2026-02-11 Wed 09:15>

* Basil is looking wilted, maybe overwatered
  <2026-02-11 Wed 17:45>
  Leaves are drooping, soil is very wet.
"""


def test_parses_entries():
    entries = parse_org_text(SAMPLE)
    assert len(entries) == 3


def test_heading_extraction():
    entries = parse_org_text(SAMPLE)
    assert entries[0].heading == "Planted tomatoes in the raised bed"
    assert entries[2].heading == "Basil is looking wilted, maybe overwatered"


def test_timestamp_extraction():
    entries = parse_org_text(SAMPLE)
    assert entries[0].timestamp == "2026-02-10 Tue 14:32"
    assert entries[1].timestamp == "2026-02-11 Wed 09:15"


def test_body_extraction():
    entries = parse_org_text(SAMPLE)
    assert entries[0].body == ""
    assert "Leaves are drooping" in entries[2].body


def test_entry_without_timestamp():
    text = "* Just a note with no timestamp\n  some body text\n"
    entries = parse_org_text(text)
    assert len(entries) == 1
    assert entries[0].timestamp is None


def test_ignores_non_heading_text():
    text = "Some preamble text\n\n* Actual heading\n  <2026-01-01 Wed 10:00>\n"
    entries = parse_org_text(text)
    assert len(entries) == 1
    assert entries[0].heading == "Actual heading"
