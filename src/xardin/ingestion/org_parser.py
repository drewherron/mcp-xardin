"""Parse org-mode files into a list of entries (heading + timestamp + body)."""

import re
from dataclasses import dataclass
from typing import Optional

# matches org timestamps like <2026-02-10 Tue 14:32>
ORG_TIMESTAMP_RE = re.compile(r"<(\d{4}-\d{2}-\d{2} \w+ \d{2}:\d{2})>")


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
        body_lines = [l for l in lines[1:] if not ORG_TIMESTAMP_RE.search(l)]
        body = "\n".join(body_lines).strip()

        # look for timestamp in any line after the heading
        timestamp = None
        for line in lines[1:]:
            m = ORG_TIMESTAMP_RE.search(line)
            if m:
                timestamp = m.group(1)
                break

        entries.append(OrgEntry(
            heading=heading,
            timestamp=timestamp,
            body=body,
            raw=chunk,
        ))

    return entries
