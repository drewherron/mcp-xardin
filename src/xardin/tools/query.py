import re

from xardin.server import mcp
from xardin.db import get_connection

# only SELECT and a few read-only pragmas are allowed
FORBIDDEN_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH)\b",
    re.IGNORECASE,
)

MAX_ROWS = 100


@mcp.tool()
def execute_query(sql: str) -> str:
    """Execute a read-only SQL query against the garden database.

    Use the garden://schema resource to see available tables and columns.
    Only SELECT statements are allowed.
    """
    if FORBIDDEN_RE.search(sql):
        return "Error: only SELECT queries are allowed."

    conn = get_connection()
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchmany(MAX_ROWS)
    except Exception as e:
        return f"Query error: {e}"

    if not rows:
        return "No results."

    # format as a simple table
    columns = [desc[0] for desc in cursor.description]
    lines = [" | ".join(columns)]
    lines.append("-+-".join("-" * len(c) for c in columns))
    for row in rows:
        lines.append(" | ".join(str(v) if v is not None else "" for v in row))

    result = "\n".join(lines)
    if len(rows) == MAX_ROWS:
        result += f"\n\n(limited to {MAX_ROWS} rows)"
    return result
