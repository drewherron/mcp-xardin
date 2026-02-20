"""Parse org-mode files into a list of entries (heading + timestamp + body)."""

import re
from dataclasses import dataclass
from typing import Optional

# <2026-02-10 Tue 14:32> or <2026-02-10 Tue> style (inline timestamps)
ACTIVE_TS_RE = re.compile(r"<(\d{4}-\d{2}-\d{2} \w+(?: \d{2}:\d{2})?)>")
# [2026-02-10 Tue 14:32] or [2026-02-10 Tue] style (inactive, used in property drawers)
INACTIVE_TS_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2} \w+(?: \d{2}:\d{2})?)\]")

PROPERTY_LINE_RE = re.compile(r"^\s*:(PROPERTIES|CREATED|END):", re.IGNORECASE)


@dataclass
class OrgEntry:
    heading: str
    timestamp: Optional[str]
    body: str
    raw: str  # full text of the entry for hashing


def parse_org_file(path: str) -> list[OrgEntry]:
    with open(path) as f:
        text = f.read()
    return parse_org_text(text)


def parse_org_text(text: str) -> list[OrgEntry]:
    """Parse org text into entries. Split on top-level headings (single *)."""
    entries = []
    chunks = re.split(r"(?=^\* )", text, flags=re.MULTILINE)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("* "):
            continue

        lines = chunk.split("\n")
        heading = lines[0].lstrip("* ").strip()

        # extract timestamp — check property drawers first, then inline
        timestamp = None
        for line in lines[1:]:
            if ":CREATED:" in line:
                m = INACTIVE_TS_RE.search(line) or ACTIVE_TS_RE.search(line)
                if m:
                    timestamp = m.group(1)
                    break
        if timestamp is None:
            for line in lines[1:]:
                m = ACTIVE_TS_RE.search(line) or INACTIVE_TS_RE.search(line)
                if m:
                    timestamp = m.group(1)
                    break

        # body is everything that isn't the heading, timestamps, or property drawer
        body_lines = []
        for line in lines[1:]:
            if PROPERTY_LINE_RE.match(line):
                continue
            if ACTIVE_TS_RE.match(line.strip()):
                continue
            if INACTIVE_TS_RE.match(line.strip()):
                continue
            body_lines.append(line)
        body = "\n".join(body_lines).strip()

        entries.append(OrgEntry(
            heading=heading,
            timestamp=timestamp,
            body=body,
            raw=chunk,
        ))

    return entries
