from xardin.ingestion.org_parser import parse_org_text


# inline timestamp style
SAMPLE_INLINE = """\
* Planted tomatoes in the raised bed
  <2026-02-10 Tue 14:32>

* Moved the pepper to the sunny spot by the fence
  <2026-02-11 Wed 09:15>

* Basil is looking wilted, maybe overwatered
  <2026-02-11 Wed 17:45>
  Leaves are drooping, soil is very wet.
"""

# property drawer style (Orgzly)
SAMPLE_PROPS = """\
* Planted tomatoes in the raised bed
:PROPERTIES:
:CREATED:  [2026-02-10 Tue 14:32]
:END:

* Basil is looking wilted
:PROPERTIES:
:CREATED:  [2026-02-11 Wed 17:45]
:END:
Leaves are drooping, soil is very wet.
"""


def test_parses_inline_entries():
    entries = parse_org_text(SAMPLE_INLINE)
    assert len(entries) == 3


def test_parses_property_entries():
    entries = parse_org_text(SAMPLE_PROPS)
    assert len(entries) == 2


def test_heading_extraction():
    entries = parse_org_text(SAMPLE_INLINE)
    assert entries[0].heading == "Planted tomatoes in the raised bed"
    assert entries[2].heading == "Basil is looking wilted, maybe overwatered"


def test_inline_timestamp():
    entries = parse_org_text(SAMPLE_INLINE)
    assert entries[0].timestamp == "2026-02-10 Tue 14:32"
    assert entries[1].timestamp == "2026-02-11 Wed 09:15"


def test_property_timestamp():
    entries = parse_org_text(SAMPLE_PROPS)
    assert entries[0].timestamp == "2026-02-10 Tue 14:32"
    assert entries[1].timestamp == "2026-02-11 Wed 17:45"


def test_body_excludes_property_drawer():
    entries = parse_org_text(SAMPLE_PROPS)
    assert "PROPERTIES" not in entries[1].body
    assert "CREATED" not in entries[1].body
    assert "Leaves are drooping" in entries[1].body


def test_body_excludes_inline_timestamp():
    entries = parse_org_text(SAMPLE_INLINE)
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
