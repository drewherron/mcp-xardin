from xardin.server import mcp
from xardin.db.schema import SCHEMA


@mcp.resource("garden://schema")
def get_schema() -> str:
    """The database schema DDL. Useful for generating SQL queries."""
    return SCHEMA
