from mcp.server.fastmcp import FastMCP

mcp = FastMCP("xardin")

# tool and resource modules register themselves via decorators on import
import xardin.tools.manage  # noqa: E402, F401
import xardin.resources  # noqa: E402, F401


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
